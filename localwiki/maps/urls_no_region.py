from django.conf.urls import *
from django.views.generic import TemplateView

from utils.constants import DATETIME_REGEXP

from .views import *
from .feeds import MapChangesFeed


urlpatterns = patterns('',
    url(r'^map/$', MapFullRegionView.as_view(), name='global'),
    url(r'^map/_nearby/?$', MapNearbyView.as_view(), name='nearby'),
    url(r'^map/_everything_everywhere$', EverythingEverywhereAsPointsView.as_view(), name='everything-as-points'),
    url(r'^map/tags/(?P<tag>.+)', MapForTag.as_view(), name='tagged'),
    url(r'^map/_objects/$', MapObjectsForBounds.as_view(), name='objects'),
    url(r'^map/_get_osm/$', OSMGeometryLookup.as_view(), name='osm-geom-lookup'),
    url(r'^map/_edit_without_page$', MapCreateWithoutPageView.as_view(),  name='edit-without-page'),
    url(r'^map/(?P<slug>.+)/_edit$', MapUpdateView.as_view(),  name='edit'),
    url(r'^map/(?P<slug>.+)/_delete$', MapDeleteView.as_view(), name='delete'),
    url(r'^map/(?P<slug>.+)/_revert/(?P<version>[0-9]+)$',
        MapRevertView.as_view(), name='revert'),

    url(r'^map/(?P<slug>.+)/_history/compare', MapCompareView.as_view()),
    url((r'^map/(?P<slug>.+)/_history/'
            r'(?P<version1>[0-9]+)\.\.\.(?P<version2>[0-9]+)?$'),
        MapCompareView.as_view(), name='compare-revisions'),
    url(r'^map/(?P<slug>.+)/_history/(?P<date1>%s)\.\.\.(?P<date2>%s)?$' %
        (DATETIME_REGEXP, DATETIME_REGEXP),
        MapCompareView.as_view(), name='compare-dates'),
    url(r'^map/(?P<slug>.+)/_history/(?P<version>[0-9]+)$',
        MapVersionDetailView.as_view(), name='as_of_version'),
    url(r'^map/(?P<slug>.+)/_history/(?P<date>%s)$' % DATETIME_REGEXP,
        MapVersionDetailView.as_view(), name='as_of_date'),
    url(r'^map/(?P<slug>.+)/_history/_feed/*$', MapChangesFeed(),
        name='changes-feed'),
    url(r'^map/(?P<slug>.+)/_history/$', MapVersionsList.as_view(),
        name='history'),
    url(r'^map/(?P<slug>(?:(?!/_).)+?)/*$', MapDetailView.as_view(),
        name='show'),
)
