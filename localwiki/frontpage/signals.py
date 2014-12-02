from django.db.models.signals import post_save
from django.core.cache import cache
from django.conf import settings
from django.core.urlresolvers import set_urlconf, get_urlconf


def _clear_frontpage(region):
    from pages.cache import varnish_invalidate_url
    from .views import FrontPageView

    current_urlconf = get_urlconf() or settings.ROOT_URLCONF
    region = region

    key = FrontPageView.get_cache_key(region=region.slug)
    cache.delete(key)

    if region.regionsettings.domain:
        # Has a domain, ugh. Need to clear two URLs on two hosts, in this case
        set_urlconf('main.urls_no_region')

        key = FrontPageView.get_cache_key(region=region.slug)
        cache.delete(key)
        varnish_invalidate_url(region.get_absolute_url(), hostname=region.regionsettings.domain)

        # Now invalidate main path on LocalWiki hub
        set_urlconf('main.urls')

        key = FrontPageView.get_cache_key(region=region.slug)
        cache.delete(key)
        varnish_invalidate_url(region.get_absolute_url())
    else:
        key = FrontPageView.get_cache_key(region=region.slug)
        cache.delete(key)
        varnish_invalidate_url(region.get_absolute_url())

    set_urlconf(current_urlconf)


def _frontpage_post_save(sender, instance, created, raw, **kwargs):
    from pages.models import Page
    from .models import FrontPage

    if sender is FrontPage:
        _clear_frontpage(instance.region)
    elif sender is Page:
        if instance.slug == 'front page':
            _clear_frontpage(instance.region)
    return


post_save.connect(_frontpage_post_save)
