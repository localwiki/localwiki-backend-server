from django.conf.urls.defaults import *
from views import *
from pages.urls import slugify
from utils.constants import DATETIME_REGEXP

urlpatterns = patterns('',
    # version history views
    url(r'^(?P<slug>.+)/_history/$', slugify(InfoboxVersions.as_view()),
        name='infobox-history'),
    url(r'^(?P<slug>.+)/_history/(?P<version>[0-9]+)$',
        slugify(InfoboxVersionDetailView.as_view()),
        name='infobox-as_of_version'),
    url(r'^(?P<slug>.+)/_history/(?P<date>%s)$'
        % DATETIME_REGEXP, slugify(InfoboxVersionDetailView.as_view()),
        name='infobox-as_of_date'),

    url(r'^(?P<slug>.+)/$', slugify(InfoboxUpdateView.as_view()),
        name='infobox'),
    url(r'^(?P<slug>.+)/add$', slugify(InfoboxAddAttributeView.as_view()),
        name='add_attribute'),

#    url(r'^(?P<slug>.+)/_history/compare',
#        slugify(InfoboxCompareView.as_view())),
#    url((r'^(?P<slug>.+)/_history/'
#         r'(?P<version1>[0-9]+)\.\.\.(?P<version2>[0-9]+)?$'),
#        slugify(InfoboxCompareView.as_view()), name='infobox-compare-revisions'),
#    url(r'^(?P<slug>.+)/_history/'
#        r'(?P<date1>%s)\.\.\.(?P<date2>%s)?$'
#        % (DATETIME_REGEXP, DATETIME_REGEXP),
#        slugify(InfoboxCompareView.as_view()), name='infobox-compare-dates'),
#     url(r'^(?P<slug>.+)/_revert/(?P<version>[0-9]+)$',
#        slugify(InfoboxRevertView.as_view()), name='infobox-revert'),

    # TODO: the following patterns need updating or removal
    #url(r'^$', AttributeListView.as_view(), name='attribute-list'),
    #url(r'^(?P<slug>.+)/$', AttributeUpdateView.as_view(), name='attribute-update'),
    #url(r'^_create$', AttributeCreateView.as_view(), name='attribute-create'),
)
