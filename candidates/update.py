# All actions taken by this front-end can be seen as person-centric.
# We use an intermediate representation (a Python dictionary) of what
# that person and their membership should look like - all views that
# need to make a change to information about a person should generate
# data in this format.
#
# These functions takes a such a dictionary and either (a) change the
# person and their memberships to match or (b) creating the person
# from this data.
#
# The dictionary represents everything we're interested in about a
# candidate's status.  It may have the following fields, which are
# straighforward and set to the empty string if unknown.
#
#   'id'
#   'full_name'
#   'email'
#   'birth_date'
#   'wikipedia_url'
#   'homepage_url'
#   'twitter_username'
#
# It should also have a 'party_memberships' member which is set to a
# dictionary.  If someone was known to be standing for the
# Conservatives in 2010 and UKIP in 2015, this would be:
#
#   'party_memberships': {
#     '2010': {
#       'name': 'Conservative Party',
#       'id': 'party:52',
#     '2015': {
#       'name': 'UK Independence Party - UKIP',
#       'id': 'party:85',
#     }
#   }
#
# If someone is standing in 2015 for Labour, but wasn't standing in
# 2010, this should be:
#
#   'party_memberships': {
#     '2015': {
#       'name': 'Labour Party',
#       'id': 'party:53',
#   }
#
# Finally, there is a 'standing_in' member which indicates if a person if
# known to be standing in 2010 or 2015:
#
# If someone was standing in 2010 in South Cambridgeshire, but nothing
# is known about 2015, this would be:
#
#   'standing_in': {
#     '2010': {
#       'name': 'South Cambridgeshire',
#       'post_id': '65922',
#       'mapit_url': 'http://mapit.mysociety.org/area/65922',
#     }
#   }
#
# If someone was standing in 2010 in Aberdeen South but is known not
# to be standing in 2015, this would be:
#
#   'standing_in': {
#     '2010': {
#        'name': 'Aberdeen South',
#        'post_id': '14399',
#        'mapit_url': 'http://mapit.mysociety.org/area/14399',
#     }
#     '2015': None,
#   }
#
# If someone was standing in Edinburgh East in 2010, but nothing is
# known about whether they're standing in 2015, this would be:
#
#   'standing_in': {
#     '2010': {
#        'name': 'Aberdeen South',
#        'post_id': '14399',
#        'mapit_url': 'http://mapit.mysociety.org/area/14399',
#     },
#   }
#
# Or if someone is known to be standing in Edinburgh East in 2010 and
# then is thought to be standing in Edinburgh North and Leith in 2015,
# this would be:
#
#   'standing_in': {
#     '2010': {
#        'name': 'Edinburgh East',
#        'post_id': '14419',
#        'mapit_url': 'http://mapit.mysociety.org/area/14419',
#     },
#     '2015': {
#        'name': 'Edinburgh North and Leith',
#        'post_id': '14420',
#        'mapit_url': 'http://mapit.mysociety.org/area/14420',
#     },
#   }

from datetime import timedelta

from .models import PopItPerson
from .static_data import MapItData, PartyData
from .models import get_person_data_from_dict
from .models import form_simple_fields, form_complex_fields_locations

from .models import election_date_2005, election_date_2010
from .models import candidate_list_name_re
from .models import create_person_with_id_retries

from .popit import PopItApiMixin

import django.dispatch
person_added = django.dispatch.Signal(providing_args=["data"])


def election_year_to_party_dates(election_year):
    if str(election_year) == '2010':
        return {
            'start_date': str(election_date_2005 + timedelta(days=1)),
            'end_date': str(election_date_2010),
        }
    elif str(election_year) == '2015':
        return {
            'start_date': str(election_date_2010 + timedelta(days=1)),
            'end_date': '9999-12-31',
        }
    else:
        raise Exception('Unknown election year: {0}'.format(election_year))

def get_value_from_location(location, person_data):
    for info in person_data[location['sub_array']]:
        if info[location['info_type_key']] == location['info_type']:
            return info.get(location['info_value_key'], '')
    return ''

def reduced_organization_data(organization):
    return {
        'id': organization['id'],
        'name': organization['name'],
    }

class PersonParseMixin(PopItApiMixin):

    """A mixin for turning PopIt data into our representation"""

    def get_person(self, person_id):
        """Get our representation of the candidate's data from a PopIt person ID"""

        result = {'id': person_id}
        person = PopItPerson.create_from_popit(self.api, person_id)
        for field in form_simple_fields:
            result[field] = person.popit_data.get(field, '')
        for field, location in form_complex_fields_locations.items():
            result[field] = get_value_from_location(location, person.popit_data)
        result['versions'] = person.popit_data.get('versions', [])

        year_to_party = person.parties
        standing_in = person.standing_in
        party_memberships = {}
        for year, standing in standing_in.items():
            party = year_to_party.get(year)
            party_2010 = year_to_party.get('2010')
            fallback_party = year_to_party.get(None)
            if party:
                party_memberships[year] = reduced_organization_data(party)
            elif fallback_party:
                party_memberships[year] = reduced_organization_data(fallback_party)
            elif year == '2015' and party_2010:
                party_memberships[year] = reduced_organization_data(party_2010)
            elif standing:
                message = "There was no party data for {0} in {1}"
                raise Exception, message.format(person_id, year)

        result['standing_in'] = standing_in
        result['party_memberships'] = party_memberships
        result['image'] = person.popit_data.get('image')
        result['proxy_image'] = person.popit_data.get('proxy_image')
        result['other_names'] = person.popit_data.get('other_names', [])
        result['identifiers'] = person.popit_data.get('identifiers', [])
        return result


# FIXME: a hacky workaround to make sure that we don't set
# dates to an empty string, which will stop the PopIt record
# being indexed by Elasticsearch.
def fix_dates(data):
    if not data['birth_date']:
        data['birth_date'] = None
    for other_name in data.get('other_names', []):
        print "other_name is:", other_name
        for key in ('start_date', 'end_date'):
            if key in other_name and not other_name[key]:
                other_name[key] = None

class PersonUpdateMixin(PopItApiMixin):
    """A mixin for updating PopIt from our representation"""

    def create_party_memberships(self, person_id, data):
        for election_year, party in data.get('party_memberships', {}).items():
            # Create the party membership:
            membership = election_year_to_party_dates(election_year)
            membership['person_id'] = person_id
            membership['organization_id'] = party['id']
            self.create_membership(**membership)

    def create_candidate_list_memberships(self, person_id, data):
        for election_year, constituency in data.get('standing_in', {}).items():
            if constituency:
                # i.e. we know that this isn't an indication that the
                # person isn't standing...
                # Create the candidate list membership:
                membership = election_year_to_party_dates(election_year)
                membership['person_id'] = person_id
                membership['post_id'] = constituency['post_id']
                membership['role'] = "Candidate"
                self.create_membership(**membership)

    def create_person(self, data, change_metadata):
        fix_dates(data)
        # Create the person:
        basic_person_data = get_person_data_from_dict(data)
        basic_person_data['standing_in'] = data['standing_in']
        basic_person_data['party_memberships'] = data['party_memberships']
        original_version = change_metadata.copy()
        original_version['data'] = data
        person_result = create_person_with_id_retries(
            self.api,
            basic_person_data,
            original_version
        )
        person_id = person_result['result']['id']
        self.create_party_memberships(person_id, data)
        self.create_candidate_list_memberships(person_id, data)
        person_added.send(sender=PopItPerson, data=data)
        return person_id

    def update_person(self, data, change_metadata, previous_versions):
        fix_dates(data)
        person_id = data['id']
        basic_person_data = get_person_data_from_dict(data)
        basic_person_data['standing_in'] = data['standing_in']
        basic_person_data['party_memberships'] = data['party_memberships']
        new_version = change_metadata.copy()
        new_version['data'] = data
        basic_person_data['versions'] = [new_version] + previous_versions
        # FIXME: this is a rather horrid workaround for:
        # https://github.com/mysociety/popit-api/issues/95
        basic_person_data_for_purging = basic_person_data.copy()
        basic_person_data_for_purging['standing_in'] = None
        basic_person_data_for_purging['party_memberships'] = None
        basic_person_data_for_purging['links'] = []
        basic_person_data_for_purging['contact_details'] = []
        basic_person_data_for_purging['other_names'] = []
        self.api.persons(person_id).put(basic_person_data_for_purging)
        # end of FIXME <-- remove when #95 is fixed
        self.api.persons(person_id).put(basic_person_data)

        person = PopItPerson.create_from_popit(self.api, data['id'])
        person.delete_memberships()

        # And then create any that should be there:
        self.create_party_memberships(person_id, data)
        self.create_candidate_list_memberships(person_id, data)
        return person.id
