from django.conf.urls import *
from tags.views import TagListView, TaggedList

urlpatterns = patterns('',
    url(r'^tags/$', TagListView.as_view(), name='list'),
    url(r'^tags/(?P<slug>.+)/*$', TaggedList.as_view(), name='tagged'),
)
