#!/usr/bin/env python

from collections import defaultdict
from datetime import date, timedelta
import json
import os
from os.path import join, realpath
import re
import requests

from popit_api import PopIt
from slugify import slugify
import yaml

directory = realpath(os.path.dirname(__file__))
configuration_file = join(directory, 'conf', 'general.yml')
with open(configuration_file) as f:
    conf = yaml.load(f)

try:

    api = PopIt(
        instance=conf['POPIT_INSTANCE'],
        hostname=conf['POPIT_HOSTNAME'],
        port=conf.get('POPIT_PORT', 80),
        api_version='v0.1',
        api_key=conf['POPIT_API_KEY']
       )

    main_json = os.path.join(
        directory,
        'data',
        'yournextmp-json_main-20140124-030234.json',
       )

    with open(main_json) as f:
        main_data = json.load(f)

    r = requests.get('http://mapit.mysociety.org/areas/WMC')
    wmc_data = r.json()

    # We want a mapping between Westminster constituency name and seat ID:
    wmc_name_to_seat = {}
    for seat_id, seat in main_data['Seat'].items():
        wmc_name_to_seat[seat['name']] = seat_id

    seat_id_to_wmc = {}
    for wmc in wmc_data.values():
        seat_id_to_wmc[wmc_name_to_seat[wmc['name']]] = wmc

    # Build a mapping between seat ID and candidate IDs:
    seat_id_to_candidacy_id = defaultdict(set)
    for candidacy_id, candidacy in main_data['Candidacy'].items():
        seat_id_to_candidacy_id[candidacy['seat_id']].add(candidacy_id)

    # Possibly not needed:
    commons_id = 'commons'
    api.organizations.post({
        'id': commons_id,
        'name': 'House of Commons',
        'classification': 'UK House of Parliament',
       })

    election_date_2005 = date(2005, 5, 5)
    election_date_2010 = date(2010, 5, 6)

    # Get all Westminster constituencies from MapIt

    r = requests.get('http://mapit.mysociety.org/areas/WMC')
    wmc_data = r.json()

    cons_to_post = {}

    for wmc in wmc_data.values():
        wmc_name = wmc['name']
        wmc_slug = slugify(wmc_name)
        api.posts.post({
            'id': str(wmc['id']),
            'label': 'Member of Parliament for ' + wmc_name,
            'role': 'Member of Parliament',
            'organization_id': commons_id,
            'start_date': str(election_date_2005 + timedelta(days=1)),
            'area': {
                'id': 'mapit:' + str(wmc['id']),
                'name': wmc['name'],
                'identifier': 'http://mapit.mysociety.org/area/' + str(wmc['id'])
            }
        })
        cons_to_post[wmc_name] = str(wmc['id'])

    # Create all the parties:
    party_id_to_organisation = {}
    for party_id, party in main_data['Party'].items():
        slug = slugify(party['name'])
        # FIXME: add identifiers
        api.organizations.post({
            'id': slug,
            'classification': 'Party',
            'name': party['name']
        })
        party_id_to_organisation[party_id] = slug

    # Create all the people, and their party memberships:
    candidate_id_to_person = {}
    for candidate_id, candidate in main_data['Candidate'].items():
        slug = candidate['code'].replace('_', '-')
        candidate_id_to_person[candidate_id] = slug
        properties = {
            'id': slug,
            'name': candidate['name'],
            'identifiers': [
                {
                    'scheme': 'yournextmp-candidate',
                    'identifier': candidate_id,
                }
            ],
        }
        dob = candidate['dob']
        if dob:
            m = re.search(r'(\d+)/(\d+)/(\d+)', dob)
            if m:
                d = date(*reversed([int(x, 10) for x in m.groups()]))
                properties['birth_date'] = str(d)
        for k in ('gender', 'email', 'phone'):
            properties[k] = candidate[k]
        api.persons.post(properties)
        api.memberships.post({
            'person_id': slug,
            'organization_id': party_id_to_organisation[candidate['party_id']],
        })

    # Go through all the candidacies and create memberships from them:
    for candidacy_id, candidacy in main_data['Candidacy'].items():
        wmc = seat_id_to_wmc[candidacy['seat_id']]
        post = cons_to_post[wmc['name']]
        if main_data['Candidate'][candidacy['candidate_id']]['status'] == 'standing':
            properties = {
                'person_id': candidate_id_to_person[candidacy['candidate_id']],
                'post_id': post,
                'role': 'Candidate',
                'start_date': str(election_date_2005 + timedelta(days=1)),
                'end_date': str(election_date_2010),
            }
            print "creating candidacy with properties:", json.dumps(properties)
            api.memberships.post(properties)

except Exception as e:
    print "got exception:", e
    if hasattr(e, 'content'):
        print "the exception body was:", e.content
    raise
