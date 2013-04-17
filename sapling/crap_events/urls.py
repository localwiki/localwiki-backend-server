from django.conf.urls.defaults import *

from views import EventListView, EventUpdateView


urlpatterns = patterns('',
    url(r'^$', EventListView.as_view(), name='list'),
    url(r'^_new', EventUpdateView.as_view(), name='new'),
)
