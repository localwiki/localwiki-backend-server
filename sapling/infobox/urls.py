from django.conf.urls.defaults import *
from views import *


urlpatterns = patterns('',
    url(r'^$', AttributeListView.as_view(), name='attribute-list'),
    url(r'^(?P<slug>.+)/$', AttributeUpdateView.as_view(), name='attribute-update'),
    url(r'^_create$', AttributeCreateView.as_view(), name='attribute-create'),
)
