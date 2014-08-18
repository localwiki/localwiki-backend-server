from django.conf.urls import *

from localwiki.utils.views import GetCSRFCookieView


urlpatterns = patterns('',
    url(r'^pages/suggest/?$', 'pages.views.suggest'),
    url(r'^regions/suggest/?$', 'regions.views.suggest'),
    url(r'^tags/suggest/?$', 'tags.views.suggest_tags'),
    url(r'^users/suggest/(?P<region>[^/]+?)/?$', 'users.views.suggest_users'),

    url(r'^_get/csrf_cookie/?$', GetCSRFCookieView.as_view(), name='get_csrf_cookie'),
)
