from django.conf.urls import *
from tags.views import TagListView, TaggedList, GlobalTaggedList, AddSingleTagView

urlpatterns = patterns('',
    url(r'^(?P<region>[^/]+?)/(?i)tags/$', TagListView.as_view(), name='list'),
    url(r'^(?P<region>[^/]+?)/(?i)tags/(?P<slug>.+)/*$', TaggedList.as_view(), name='tagged'),
    url(r'^(?P<region>[^/]+?)/_add_tag/$', AddSingleTagView.as_view(), name='add-single'),

    url(r'^tags/(?P<slug>.+)/*$', GlobalTaggedList.as_view(), name='global-tagged'),
)
