import time

from django.utils.decorators import classonlymethod
from django.http import HttpResponse, Http404, HttpResponseForbidden
from django.utils import simplejson as json
from django.utils.decorators import method_decorator
from django.views.decorators.vary import vary_on_headers as dj_vary_on_headers
from django.views.decorators.cache import never_cache
from django.views.generic import View, RedirectView, TemplateView
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.core.cache import cache
from django.http import HttpRequest
from django.utils.cache import get_cache_key
from django.template.loader import render_to_string
from django.template.context import RequestContext

from fancy_cache import cache_page

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
    # By default, set it to a huge timeout due to Django (and now, django-fancy-cache) confusion around timeout parameter here.
    # TODO: Set this to either None or 0 once we're on Django 1.7 AND once django-fancy-cache has fixed it's 0/None timeout
    #       issue.
    cache_timeout = DEFAULT_MEMCACHED_TIMEOUT  
    # For now, we default to Vary on the Host header.
    # This is because Django 1.5 doesn't (yet) automatically
    # generate cache keys based on the full URI - only the path.
    #
    # TODO: In Django 1.7 this can be removed, as the full URI
    #       is used in the cache key.
    vary_on_headers = ['Host']
    get_cache_prefix = None
    cache_keep_forever = False
     
    def dispatch(self, *args, **kwargs):
        # Have to create this closure b/c args aren't being passed
        # correctly to the passed cache prefix function for some
        # reason.
        def _get_cache_prefix(request, *ignore_args, **ignore_kwargs):
            if not self.get_cache_prefix:
                return None
            return self.get_cache_prefix(*args, **kwargs)

        f = cache_page(self.cache_timeout, key_prefix=_get_cache_prefix)(super(CacheMixin, self).dispatch)
        if self.vary_on_headers:
            f = dj_vary_on_headers(*self.vary_on_headers)(f)

        request = args[0]
        r = f(*args, **kwargs)
        if self.cache_keep_forever:
            r['X-KEEPME'] = True
        return r


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
