from django.conf.urls import *

from .views import MainPageView

urlpatterns = patterns('',
    url(r'^/*$', MainPageView.as_view(), name='main-page'),
)
