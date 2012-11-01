from django.conf.urls.defaults import *
from views import *
from pages.urls import slugify

urlpatterns = patterns('',
    # version history views
    url(r'^(?P<slug>.+)/_history/$', slugify(InfoboxVersions.as_view()),
        name='infobox-history'),

    url(r'^(?P<slug>.+)/$', slugify(InfoboxUpdateView.as_view()),
        name='infobox'),
    url(r'^(?P<slug>.+)/add$', slugify(InfoboxAddAttributeView.as_view()),
        name='add_attribute'),

    # TODO: the following patterns need updating or removal
    #url(r'^$', AttributeListView.as_view(), name='attribute-list'),
    #url(r'^(?P<slug>.+)/$', AttributeUpdateView.as_view(), name='attribute-update'),
    #url(r'^_create$', AttributeCreateView.as_view(), name='attribute-create'),
)
