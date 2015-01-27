from django.conf.urls import patterns, url

from polls.views import ConstituencyDetailView

urlpatterns = patterns('',
    url(r'^constituency/(?P<mapit_area_id>\d+)/(?P<ignored_slug>.*)$',
        ConstituencyDetailView.as_view(),
        name='constituency'),
)
