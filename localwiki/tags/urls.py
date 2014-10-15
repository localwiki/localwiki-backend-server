from django.conf.urls import *
from tags.views import TagListView, TaggedList, GlobalTaggedList

urlpatterns = patterns('',
    url(r'^(?P<region>[^/]+?)/tags/$', TagListView.as_view(), name='list'),
    url(r'^(?P<region>[^/]+?)/tags/(?P<slug>.+)/*$', TaggedList.as_view(), name='tagged'),

    url(r'^tags/(?P<slug>.+)/*$', GlobalTaggedList.as_view(), name='global-tagged'),
)
