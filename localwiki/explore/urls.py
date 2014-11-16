from django.conf.urls import *
from django.views.decorators.cache import cache_page

from localwiki.utils.views import NamedRedirectView
from maps.widgets import InfoMap

from .views import RandomExploreList, AlphabeticalExploreList, ExploreJustList, RandomTourJSON, RandomTourView


urlpatterns = patterns('',
    url(r'^_explore/?$', RandomExploreList.as_view(), name='explore'),
    url(r'^_explore/alphabetical/?$', AlphabeticalExploreList.as_view(), name='explore-alphabetical'),
    url(r'^_explore/list/?$', ExploreJustList.as_view(), name='explore-as-list'),
    url(r'^_explore/rtour_json/?$', cache_page(300)(RandomTourJSON.as_view()), name='random-tour-json'),
    url(r'^_explore/rtour/?$', cache_page(300)(RandomTourView.as_view()), name='random-tour'),

    ##########################################################
    # Redirects to preserve old URLs
    ########################################################## 
    url(r'^(?i)All_Pages/*$', NamedRedirectView.as_view(name='explore-as-list')),
)
