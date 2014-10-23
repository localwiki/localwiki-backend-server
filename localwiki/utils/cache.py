from functools import wraps

from django.views.decorators.cache import cache_page as dj_cache_page
from django.utils.decorators import decorator_from_middleware_with_args, available_attrs


def cache_page(*o_args, **o_kwargs):
    def _add_host_to_key_prefix(host, o_kwargs):
        key_prefix = o_kwargs.get('key_prefix', '')
        if key_prefix and not key_prefix.startswith('%s:' % host):
            key_prefix = '%s:%s:' % (host, key_prefix)
        else:
            key_prefix = '%s:' % host
        o_kwargs['key_prefix'] = key_prefix

    def _cache_page(viewfunc):
        @wraps(viewfunc, assigned=available_attrs(viewfunc))
        def _cache_paged(request, *args, **kw):
            host = request.META.get('HTTP_HOST')
            _add_host_to_key_prefix(host, o_kwargs)
            f = dj_cache_page(*o_args, **o_kwargs)
            f = f(viewfunc)
            return f(request, *args, **kw)
        return _cache_paged
    return _cache_page
