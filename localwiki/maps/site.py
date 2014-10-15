from maps.urls import urlpatterns
from maps.urls_no_region import urlpatterns as urlpatterns_no_region


urls = (urlpatterns, 'maps', 'maps')
urls_no_region = (urlpatterns_no_region, 'maps', 'maps')
