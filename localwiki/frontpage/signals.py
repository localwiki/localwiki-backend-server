from django.db.models.signals import post_save
from django.core.cache import cache
from django.core.urlresolvers import set_urlconf, get_urlconf


def _frontpage_post_save(sender, instance, created, raw, **kwargs):
    from pages.models import Page
    from pages.cache import varnish_invalidate_url
    from .views import FrontPageView

    if sender is not Page:
        return

    if instance.slug == 'front page':
        current_urlconf = get_urlconf() or settings.ROOT_URLCONF
        region = instance.region

        key = FrontPageView.get_cache_key(region=instance.region.slug)
        cache.delete(key)

        if region.regionsettings.domain:
            # Has a domain, ugh. Need to clear two URLs on two hosts, in this case
            set_urlconf('main.urls_no_region')
            varnish_invalidate_url(region.get_absolute_url(), hostname=region.regionsettings.domain)

            # Now invalidate main path on LocalWiki hub
            set_urlconf('main.urls')
            varnish_invalidate_url(region.get_absolute_url())
        else:
            varnish_invalidate_url(region.get_absolute_url())

        set_urlconf(current_urlconf)


post_save.connect(_frontpage_post_save)
