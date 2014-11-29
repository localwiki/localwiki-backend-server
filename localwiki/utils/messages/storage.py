from django.conf import settings
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.messages.storage.cookie import CookieStorage
from django.contrib.messages.storage.session import SessionStorage


class CookieStorageCrossDomain(CookieStorage):
    def _update_cookie(self, encoded_data, response):
        hostname = self.request.META.get('HTTP_HOST', '').split(':')[0]
        session_domain = settings.SESSION_COOKIE_DOMAIN
        if session_domain.endswith(hostname):
            domain = session_domain
        else:
            domain = ''

        if encoded_data:
            response.set_cookie(self.cookie_name, encoded_data,
                domain=domain)
        else:
            response.delete_cookie(self.cookie_name,
                domain=domain)


class FallbackStorageCrossDomain(FallbackStorage):
    storage_classes = (CookieStorageCrossDomain, SessionStorage)
