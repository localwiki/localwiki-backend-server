from django.conf.urls import *

from .views import LinksForPageView, OrphanedPagesView

urlpatterns = patterns('',
    url(r'^_orphaned/(?P<region>[^/]+?)/?$',
        OrphanedPagesView.as_view(), name='orphaned'),
    url(r'^(?P<region>[^/]+?)/(?P<slug>.+)/$',
        LinksForPageView.as_view(), name='for-page'),
)
