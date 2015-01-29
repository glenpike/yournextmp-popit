from django.core.urlresolvers import reverse
from django.db import models
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.http import urlquote
from django.views.generic import TemplateView
from candidates.popit import PopItApiMixin

from candidates.models import (
    PopItPerson,
    get_constituency_name_from_mapit_id,
    membership_covers_date, election_date_2015
)

from polls.models import Vote

# Create your views here.
def get_constituency_data(api, mapit_area_id, context):
    context['mapit_area_id'] = mapit_area_id
    context['constituency_name'] = \
        get_constituency_name_from_mapit_id(mapit_area_id)

    # context['electionleaflets_url'] = \
    #     get_electionleaflets_url(context['constituency_name'])

    mp_post = api.posts(mapit_area_id).get(
        embed='membership.person.membership.organization')

    current_candidates = set()

    for membership in mp_post['result']['memberships']:
        if not membership['role'] == "Candidate":
            continue
        person = PopItPerson.create_from_dict(membership['person_id'])
        # if membership_covers_date(membership, election_date_2010):
        #     pass
        if membership_covers_date(membership, election_date_2015):
            current_candidates.add(person)
        else:
            pass

    context['candidates_2015'] = current_candidates

def novote(request, mapit_area_id):
    #Make sure Popit area exists
    constituency_name = get_constituency_name_from_mapit_id(mapit_area_id)
    if constituency_name is None:
        return render(request, 'polls/error.html', {
            'error_message': "You didn't select a constituency.",
            })
    else:
        #If so add a Vote with -1 as candidate
        v = Vote(constituency_id=mapit_area_id, candidate_id=-1, party_id=-1)
        v.save();
        return HttpResponseRedirect(reverse('results', args=(mapit_area_id,)))

def vote(request, mapit_area_id):
    #Make sure Popit area exists
    constituency_name = get_constituency_name_from_mapit_id(mapit_area_id)
    if constituency_name is None:
        return render(request, 'polls/error.html', {
            'error_message': "You didn't select a constituency.",
            })
    else:
        #If so make sure Popit Person exists
            #Add a Vote

        return HttpResponseRedirect(reverse('results', args=(mapit_area_id,)))

class ConstituencyResultsView(PopItApiMixin, TemplateView):
    template_name = 'polls/results.html'

    def get_context_data(self, **kwargs):
        context = super(ConstituencyResultsView, self).get_context_data(**kwargs)
        mapit_area_id = kwargs['mapit_area_id']
        get_constituency_data(self.api, mapit_area_id, context)

        votes = Vote.objects.filter(constituency_id=mapit_area_id).values('candidate_id').annotate(n=models.Count("pk"))
        context['votes'] = votes
        #Need to munge the data here - this is not currently a "count"

        return context

class ConstituencyDetailView(PopItApiMixin, TemplateView):
    template_name = 'polls/constituency.html'

    def get_context_data(self, **kwargs):
        context = super(ConstituencyDetailView, self).get_context_data(**kwargs)

        get_constituency_data(self.api, kwargs['mapit_area_id'], context)

        return context
