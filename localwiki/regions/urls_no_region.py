from django.conf.urls import *

from regions.views import (RegionCreateView, RegionPostSaveLogInView, RegionExploreView,
    RegionListView, RegionListMapView, RegionSettingsView, RegionAdminsUpdate, RegionBannedUpdate)


urlpatterns = patterns('',
    url(r'^_settings/?$', RegionSettingsView.as_view(), name="settings"),
    url(r'^_settings/admins/?$', RegionAdminsUpdate.as_view(), name="edit-admins"),
    url(r'^_settings/banned/?$', RegionBannedUpdate.as_view(), name="edit-banned"),
)
