from django.conf.urls import patterns, url

from polls.views import ConstituencyDetailView, ConstituencyResultsView, vote, novote

urlpatterns = patterns('',
    url(r'^results/(?P<mapit_area_id>\d+)/$',
        ConstituencyResultsView.as_view(),
        name='results'),
    #fixme - find how to hoist the "polls/" slug up to mysite.urls
    url(r'^polls/(?P<mapit_area_id>\d+)/(?P<ignored_slug>.*)$',
        ConstituencyDetailView.as_view(),
        name='polls'),

    url(r'^vote/(?P<mapit_area_id>\d+)/$',
        vote,
        name='vote'),

    url(r'^novote/(?P<mapit_area_id>\d+)/$',
        novote,
        name='novote'),
)
