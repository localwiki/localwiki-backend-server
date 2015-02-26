from .urls import urlpatterns
from .urls_no_region import urlpatterns as urlpatterns_no_region


urls = (urlpatterns, 'regions', 'regions')
urls_no_region = (urlpatterns_no_region, 'regions', 'regions')
