from django.shortcuts import render
from django.utils.http import urlquote
from django.views.generic import TemplateView
from candidates.popit import PopItApiMixin

from candidates.models import (
    PopItPerson,
    get_constituency_name_from_mapit_id,
    membership_covers_date, election_date_2015
)
# Create your views here.

class ConstituencyDetailView(PopItApiMixin, TemplateView):
    template_name = 'polls/constituency.html'

    def get_context_data(self, **kwargs):
        context = super(ConstituencyDetailView, self).get_context_data(**kwargs)

        context['mapit_area_id'] = mapit_area_id = kwargs['mapit_area_id']
        context['constituency_name'] = \
            get_constituency_name_from_mapit_id(mapit_area_id)

        # context['electionleaflets_url'] = \
        #     get_electionleaflets_url(context['constituency_name'])

        # context['redirect_after_login'] = \
        #     urlquote(reverse('constituency', kwargs={
        #         'mapit_area_id': mapit_area_id,
        #         'ignored_slug': slugify(context['constituency_name'])
        #     }))

        mp_post = self.api.posts(mapit_area_id).get(
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
                # raise ValueError("Candidate membership doesn't cover any \
                #                   known election date")

        context['candidates_2015'] = current_candidates

        # context['add_candidate_form'] = NewPersonForm(
        #     initial={'constituency': mapit_area_id}
        # )

        return context
