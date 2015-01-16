from django.core.management.base import BaseCommand

import json
from lxml import objectify

from candidates.popit import create_popit_api_object
from candidates.update import PersonParseMixin, PersonUpdateMixin
from candidates.views import CandidacyMixin

CONSTITUENCIES_JSON_FILE = 'data/mapit-WMC-generation-22.json'
ALL_MEMBERS_XML_FILE = 'data/parlparse/members/all-members-2010.xml'
PEOPLE_XML_FILE = 'data/parlparse/members/people.xml'


class Command(PersonParseMixin, PersonUpdateMixin, CandidacyMixin, BaseCommand):
    help = "Update candidates' parlparse id"

    def handle(self, *args, **options):
        self.verbosity = int(options.get('verbosity', 1))
        self.popit = create_popit_api_object()
        with open(CONSTITUENCIES_JSON_FILE) as f:
            constituencies = json.load(f).values()
        xml = objectify.parse(ALL_MEMBERS_XML_FILE).getroot()
        self.members = [member.attrib for member in xml.findall('member')]
        people_xml = objectify.parse(PEOPLE_XML_FILE).getroot()
        people = people_xml.findall('person')
        self.id_mapping = {p.get('latestname'): p.get('id') for p in people}
        self.update_candidates(constituencies)

    def update_candidates(self, constituencies):
        for constituency in constituencies:
            for member in self.members_for(constituency['name']):
                self.add_parlparse_id_to_member(member)

    def members_for(self, constituency_name):
        constituency_members = []
        for member in self.members:
            if member['constituency'] == constituency_name:
                constituency_members.append(member)
        return constituency_members

    def add_parlparse_id_to_member(self, member):
        # Try and find the corresponding person in the popit instance
        name = u'{} {}'.format(member['firstname'], member['lastname'])
        query = u'"{}"'.format(name)
        r = self.popit.api.search.persons.get(q=query)['result']
        # Have we not got exactly one result?
        if len(r) is not 1:
            if self.verbosity > 0:
                msg = u'Got {} results for {}, skipping'
                self.stderr.write(msg.format(len(r), name))
            return
        parlparse_id = self.id_mapping[name]
        person_data = self.get_person(r[0]['id'])
        previous_versions = person_data.pop('versions')
        identifiers = person_data.get('identifiers', [])
        existing_identifiers = [i['identifier'] for i in identifiers]
        # Does that person already have this identifier?
        if parlparse_id in existing_identifiers:
            if self.verbosity > 1:
                msg = u'Found existing identifier for {} ({}), skipping'
                self.stderr.write(msg.format(name, parlparse_id))
            return
        identifier = {
            'identifier': parlparse_id,
            'scheme': 'uk.org.publicwhip'
        }
        identifiers.append(identifier)
        person_data['identifiers'] = identifiers
        change_metadata = self.get_change_metadata(
            None,
            'Updated candidate with parlparse person id',
        )
        self.update_person(
            person_data,
            change_metadata,
            previous_versions,
        )
        if self.verbosity > 0:
            msg = u"Successfully updated {} with {}"
            self.stdout.write(msg.format(name, parlparse_id))
