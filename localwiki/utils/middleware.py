import threading
import time
import re

from django.utils.cache import patch_vary_headers
from django.utils.http import cookie_date
from django.db import transaction
from django.contrib.sessions.middleware import SessionMiddleware
from django.conf import settings
from django.utils import translation

class XForwardedForMiddleware():
    """
    For our Varnish configuration.
    """
    def process_request(self, request):
        if 'HTTP_X_FORWARDED_FOR' in request.META:
            parts = request.META['HTTP_X_FORWARDED_FOR'].split(',')
            if len(parts) > 1:
                # Get the second-to-last, in our case. Skip varnish (the last value)
                ip = parts[-2].strip()
            else:
                ip = parts[0]
            request.META['REMOTE_ADDR'] = ip
        return None


class AutoTrackUserInfoMiddleware(object):
    """
    Optional middleware to automatically add the current request user's
    information into the historical model as it's saved.
    """
    # If we wanted to track more than ip, user then we could use a
    # passed-in callable for logic.
    def process_request(self, request):
        if request.method in IGNORE_USER_INFO_METHODS:
            pass

        _threadlocal.request = request
        signals.pre_save.connect(self.update_fields, weak=False)

    def _lookup_field_value(self, field):
        request = _threadlocal.request
        if isinstance(field, AutoUserField):
            if hasattr(request, 'user') and request.user.is_authenticated():
                return request.user
        elif isinstance(field, AutoIPAddressField):
            return request.META.get('REMOTE_ADDR', None)

    def update_fields(self, sender, instance, **kws):
        for field in instance._meta.fields:
            # Find our automatically-set-fields.
            if isinstance(field, AutoSetField):
                # only set the field if it's currently empty
                if getattr(instance, field.attname) is None:
                    val = self._lookup_field_value(field)
                    setattr(instance, field.name, val)


class SubdomainLanguageMiddleware(object):
    """
    Set the language for the site based on the subdomain the request
    is being served on. For example, serving on 'fr.domain.com' would
    make the language French (fr).
    """
    LANGUAGES = [i[0] for i in settings.LANGUAGES]

    def process_request(self, request):
        host = request.get_host().split('.')
        if host and host[0] in self.LANGUAGES:
            lang = host[0]
        else:
            # Set to default language
            lang = settings.LANGUAGE_CODE
        translation.activate(lang)
        request.LANGUAGE_CODE = lang


class SessionMiddleware(SessionMiddleware):
    """
    A variant of SessionMiddleware that plays nicely with
    non-canonical LocalWiki (rare) custom domain names.
    """
    def process_response(self, request, response):
        session_cookie_domain = settings.SESSION_COOKIE_DOMAIN
        hostname = request.META.get('HTTP_HOST', '').split(':')[0]
        if session_cookie_domain:
            if not hostname.startswith(session_cookie_domain.lstrip('.')):
                # Set to empty to allow the cookie to be set. This means
                # subdomains aren't allowed here.
                session_cookie_domain = ''

        # Copied from SessionMiddleware (can't subclass due to hard-coded settings)
        try:
            accessed = request.session.accessed
            modified = request.session.modified
        except AttributeError:
            pass
        else:
            if accessed:
                patch_vary_headers(response, ('Cookie',))
            if modified or settings.SESSION_SAVE_EVERY_REQUEST:
                if request.session.get_expire_at_browser_close():
                    max_age = None
                    expires = None
                else:
                    max_age = request.session.get_expiry_age()
                    expires_time = time.time() + max_age
                    expires = cookie_date(expires_time)
                # Save the session data and refresh the client cookie.
                # Skip session save for 500 responses, refs #3881.
                if response.status_code != 500:
                    request.session.save()
                    response.set_cookie(settings.SESSION_COOKIE_NAME,
                            request.session.session_key, max_age=max_age,
                            expires=expires, domain=session_cookie_domain,
                            path=settings.SESSION_COOKIE_PATH,
                            secure=settings.SESSION_COOKIE_SECURE or None,
                            httponly=settings.SESSION_COOKIE_HTTPONLY or None)
        return response


#class ClearSessionMiddleware(object):
#    def process_request(self, request):
#        import pdb;pdb.set_trace()
#        self._clear_session = False
#
#        if request.session.keys() or request.user.is_authenticated():
#            return
#
#        cookie = getattr(settings, 'SESSION_COOKIE_NAME', 'sessionid')
#        if request.COOKIES.get(cookie, None):
#            self._clear_session = True
#
#    def process_response(self, request, response):
#        from regions.models import Region
#        import pdb;pdb.set_trace()
#        if self._clear_session:
#            cookie = getattr(settings, 'SESSION_COOKIE_NAME', 'sessionid')
#            session_cookie_domain = settings.SESSION_COOKIE_DOMAIN
#            hostname = request.META.get('HTTP_HOST', '')
#            if session_cookie_domain:
#                # Using a custom domain
#                if Region.objects.filter(regionsettings__domain=hostname):
#                    session_cookie_domain = '.%s' % hostname.split(':')[0]
#                elif not hostname.startswith(session_cookie_domain.lstrip('.')):
#                    session_cookie_domain = ''
#            response.delete_cookie(cookie, path=settings.SESSION_COOKIE_PATH, domain=session_cookie_domain)
#
#        return response


# NOTE: Thread-local is usually a bad idea.  However, in this case
# it is the most elegant way for us to store per-request data
# and retrieve it from somewhere else.  Our goal is to allow a
# signal to have access to the request hostname.  The alternative
# here would be hard-coding the hostname in settings, but this
# is a bit better because we can e.g. detect if we're using
# HTTPS or not.
_threadlocal = threading.local()


class RequestURIMiddleware(object):
    """
    Get and save the current host's base URI.  Contains no trailing slash.
    """
    def process_request(self, request):
        _threadlocal.base_uri = request.build_absolute_uri('/')[:-1]


class TransactionMiddleware(object):
    """
    Just like django.middleware.transaction.TransactionMiddleware, except this
    commits the lingering transaction regardless of whether or not it's `dirty`.

    Please see http://thebuild.com/blog/2010/10/25/django-and-postgresql-idle-in-transaction-connections/
    for rationale.

    TODO: XXX: NOTE: Revamp / rework this once on Django 1.6, which has a different transaction
        handling default.
    """
    def process_request(self, request):
        transaction.enter_transaction_management()
        transaction.managed(True)

    def process_exception(self, request, exception):
        transaction.rollback()
        transaction.leave_transaction_management()

    def process_response(self, request, response):
        if transaction.is_managed():
            transaction.commit()
            transaction.leave_transaction_management()
        return response
