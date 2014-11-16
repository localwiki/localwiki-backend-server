from django.conf.urls import *
from django.views.decorators.cache import cache_page

from .views import RandomTourJSON, RandomTourView


urlpatterns = patterns('',
    url(r'^_explore/rtour_json/?$', cache_page(300)(RandomTourJSON.as_view()), name='global-random-tour-json'),
    url(r'^_explore/rtour/?$', cache_page(300)(RandomTourView.as_view()), name='global-random-tour'),
)
