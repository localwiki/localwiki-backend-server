from django.conf.urls import *

from .views import RandomTourJSON, RandomTourView


urlpatterns = patterns('',
    url(r'^_explore/rtour_json/?$', RandomTourJSON.as_view(), name='global-random-tour-json'),
    url(r'^_explore/rtour/?$', RandomTourView.as_view(), name='global-random-tour'),
)
