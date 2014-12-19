from django.conf.urls.defaults import *

from views import AddCommentView


urlpatterns = patterns('',
    url(r'^(?P<slug>.+)/_add$',
        AddCommentView.as_view(), name='add'),
)
