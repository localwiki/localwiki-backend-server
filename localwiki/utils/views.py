import time

from django.utils.decorators import classonlymethod
from django.conf import settings
from django.http import HttpResponse, Http404, HttpResponseForbidden, HttpResponseServerError
from django.utils import simplejson as json
from django.utils.decorators import method_decorator
from django.views.decorators.vary import vary_on_headers as dj_vary_on_headers
from django.views.decorators.cache import never_cache
from django.views.generic import View, RedirectView, TemplateView
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.core.cache import cache
from django.views.decorators.csrf import requires_csrf_token
from django.template import (Context, loader, TemplateDoesNotExist)
from django.utils.cache import get_max_age
from django.http import HttpRequest
from django.template.loader import render_to_string
from django.template.context import RequestContext

from versionutils.versioning.views import RevertView, DeleteView

from . import take_n_from

# 29 days, effectively infinite in cache years
# XXX NOTE: For some reason, the memcached client we're using
# gives a client error when sending timestamp-style expiration
# dates -- e.g. > 30 days timestamps. So, for now we must make
# sure and always use <= 30 day timeouts, which should be fine.
DEFAULT_MEMCACHED_TIMEOUT = 60 * 60 * 24 * 29


class ForbiddenException:
    pass


class NeverCacheMixin(object):
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        return super(NeverCacheMixin, self).dispatch(*args, **kwargs)


class CacheMixin(object):
    cache_timeout = DEFAULT_MEMCACHED_TIMEOUT
    cache_keep_forever = False

    @staticmethod
    def get_cache_key(*args, **kwargs):
        raise NotImplementedError

    def _should_cache(self, request, response):
        if response.streaming or response.status_code != 200:
            return False

        # Don't cache responses that set a user-specific (and maybe security
        # sensitive) cookie in response to a cookie-less request.
        if not request.COOKIES and response.cookies and has_vary_header(response, 'Cookie'):
            return False

        if get_max_age(response) == 0:
            return False

        return True

    def _get_from_cache(self, method, request, *args, **kwargs):
        key = self.get_cache_key(request, *args, **kwargs)

        response = cache.get(key)
        if response is None:
            response = getattr(super(CacheMixin, self), method)(request, *args, **kwargs)

            if hasattr(response, 'render') and callable(response.render):
                response.add_post_render_callback(
                    lambda r: cache.set(key, r, self.cache_timeout)
                )
            else:
                cache.set(key, response, self.cache_timeout)

        if self._should_cache(request, response):
            # Mark to keep around in Varnish and other cache layers
            if self.cache_keep_forever:
                response['X-KEEPME'] = True

        return response

    def get(self, request, *args, **kwargs):
        return self._get_from_cache('get', request, *args, **kwargs)

    def head(self, request, *args, **kwargs):
        return self._get_from_cache('head', request, *args, **kwargs)


class Custom404Mixin(object):
    @classonlymethod
    def as_view(cls, **initargs):
        default_view = super(Custom404Mixin, cls).as_view(**initargs)

        def view_or_handler404(request, *args, **kwargs):
            self = cls(**initargs)
            try:
                return default_view(request, *args, **kwargs)
            except Http404 as e:
                if hasattr(self, 'handler404'):
                    return self.handler404(request, *args, **kwargs)
                raise e
        return view_or_handler404


class CreateObjectMixin(object):
    def create_object(self):
        self.form_class._meta.model()

    def get_object(self, queryset=None):
        try:
            return super(CreateObjectMixin, self).get_object(queryset)
        except Http404:
            return self.create_object()


class JSONResponseMixin(object):
    def render_to_response(self, context):
        "Returns a JSON response containing 'context' as payload"
        return self.get_json_response(self.convert_context_to_json(context))

    def get_json_response(self, content, **httpresponse_kwargs):
        "Construct an `HttpResponse` object."
        return HttpResponse(content, content_type='application/json',
                            **httpresponse_kwargs)

    def convert_context_to_json(self, context):
        """
        Convert the context dictionary into a JSON object.
        Note: Make sure that the entire context dictionary is serializable
        """
        return json.dumps(context)


class JSONView(View, JSONResponseMixin):
    """
    A JSONView returns, on GET, a json dictionary containing the values of
    get_context_data().
    """
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class PermissionRequiredMixin(object):
    """
    View mixin for verifying permissions before updating an existing object

    Attrs:
        permission: A string representing the permission that's required
           on the object.  E.g. 'page.change_page'.  Override
           permission_for_object() to allow more complex permission
           relationships.
        forbidden_message: A string to display when the permisson is not
            allowed.
    """
    permission = None
    forbidden_message = _('Sorry, you are not allowed to perform this action.')
    forbidden_message_anon = _('Anonymous users may not perform this action. '
                              'Please <a href="/Users/login/">log in</a>.')

    def get_protected_object(self):
        """
        Returns the object that should be used to check permissions.
        Override this to use a different object as the "guard".
        """
        return self.object

    def get_protected_objects(self):
        """
        Returns the objects that should be used to check permissions.
        """
        return [self.get_protected_object()]

    def permission_for_object(self, obj):
        """
        Gets the permission that's required for `obj`.
        Override this to allow more complex permission relationships.
        """
        return self.permission

    def get_object_idempotent(self):
        return self.object

    def patch_get_object(self):
        # Since get_object will get called again, we want it to be idempotent
        self.get_object = self.get_object_idempotent

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        self.args = args
        self.kwargs = kwargs
        if hasattr(self, 'get_object'):
            self.object = self.get_object()
            self.patch_get_object()
        protected_objects = self.get_protected_objects()
        for obj in protected_objects:
            if not request.user.has_perm(self.permission_for_object(obj), obj):
                if request.user.is_authenticated():
                    msg = self.forbidden_message
                else:
                    msg = self.forbidden_message_anon
                html = render_to_string('403.html', {'message': msg},
                                       RequestContext(request))
                return HttpResponseForbidden(html)
        return super(PermissionRequiredMixin, self).dispatch(request, *args,
                                                        **kwargs)

class NamedRedirectView(RedirectView):
    name = None

    def get_redirect_url(self, **kwargs):
        return reverse(self.name, kwargs=kwargs)


class AuthenticationRequired(object):
    """
    Mixin to make a view only usable to authenticated users.
    """
    forbidden_message = _('Sorry, you are not allowed to perform this action.')

    def get_forbidden_message(self):
        return self.forbidden_message

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        self.args = args
        self.kwargs = kwargs

        if self.request.user.is_authenticated():
            return super(AuthenticationRequired, self).dispatch(request, *args, **kwargs)

        msg = self.get_forbidden_message()
        html = render_to_string('403.html', {'message': msg}, RequestContext(request))
        return HttpResponseForbidden(html)


class GetCSRFCookieView(TemplateView):
    template_name = 'utils/get_csrf_cookie.html'


class MultipleTypesPaginatedView(TemplateView):
    items_per_page = 50
    context_object_name = 'objects'

    def get_object_lists(self):
        raise NotImplementedError

    def get_pagination_key(self, qs):
        """
        Args:
            qs: The queryset or iterable we want to get the querystring lookup key for.

        Returns:
            The querystring lookup.  By default, this is `qs.model.__name__.lower()`
        """
        return qs.model.__name__.lower()

    def get_pagination_merge_key(self):
        """
        Returns:
            A callable that, when called, returns the value to use for the merge +
            sort.  Default: no further sorting (stay in place).
        """
        return None

    def get_pagination_objects(self):
        items_with_indexes = []
        id_to_page_key = {}
        for (_id, qs) in enumerate(self.get_object_lists()):
            pagination_key = self.get_pagination_key(qs)
            page = int(self.request.GET.get(pagination_key, 0))
            items_with_indexes.append((qs, page))
            id_to_page_key[_id] = pagination_key

        items, indexes, has_more_left = take_n_from(
            items_with_indexes,
            self.items_per_page,
            merge_key=self.get_pagination_merge_key()
        )
        self.has_more_left = has_more_left

        self.current_indexes = {}
        for (num, index) in enumerate(indexes):
            self.current_indexes[id_to_page_key[num]] = index

        return items

    def get_context_data(self, *args, **kwargs):
        c = super(MultipleTypesPaginatedView, self).get_context_data(*args, **kwargs)

        c[self.context_object_name] = self.get_pagination_objects()
        c['pagination_has_more_left'] = self.has_more_left
        c['pagination_next'] = ''
        if self.has_more_left:
            qitems = []
            for pagelabel, index in self.current_indexes.items():
                qitems.append('%s=%s' % (pagelabel, index))
            c['pagination_next'] = '?' + '&'.join(qitems)

        return c


class RevertView(RevertView):
    def allow_admin_actions(self):
        return self.request.user.is_staff


class DeleteView(DeleteView):
    def allow_admin_actions(self):
        return self.request.user.is_staff


@requires_csrf_token
def server_error(request, template_name='500.html'):
    """
    500 error handler.

    Templates: :template:`500.html`
    Context: Contains {{ STATIC_URL }} and {{ LANGUAGE_CODE }}
    """
    try:
        template = loader.get_template(template_name)
    except TemplateDoesNotExist:
        return HttpResponseServerError('<h1>Server Error (500)</h1>')
    return HttpResponseServerError(template.render(Context({
        'STATIC_URL': settings.STATIC_URL,
        'LANGUAGE_CODE': settings.LANGUAGE_CODE,
    })))
