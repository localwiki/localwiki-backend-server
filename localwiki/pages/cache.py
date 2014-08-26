from django.conf import settings
from django.core.urlresolvers import set_urlconf, get_urlconf
from django.core.cache import cache

from celery import shared_task
from varnish import VarnishManager


def varnish_invalidate_page(p):
    ban_path = r'obj.http.x-url ~ ^(?i)(%(url)s(/*)(\\?.*)?)$ && obj.http.x-host ~ ^((?i)(.*\\.)?%(host)s(:[0-9]*)?)$'

    current_urlconf = get_urlconf()

    if p.region.regionsettings.domain:
        # Has a domain, ugh. Need to clear two URLs on two hosts, in this case
        set_urlconf('main.urls_no_region')
        url = p.get_absolute_url()
        ban_cmd = (ban_path % {'url': url, 'host': p.region.regionsettings.domain}).encode('ascii')
        manager = VarnishManager(settings.VARNISH_MANAGEMENT_SERVERS)
        manager.run('ban', ban_cmd, secret=settings.VARNISH_SECRET)

        # Now invalidate main path on LocalWiki hub
        set_urlconf('main.urls')
        url = p.get_absolute_url()
        ban_cmd = ban_path % {'url': url, 'host': settings.MAIN_HOSTNAME}
        manager = VarnishManager(settings.VARNISH_MANAGEMENT_SERVERS)
        manager.run('ban', ban_cmd, secret=settings.VARNISH_SECRET)
    else:
        url = p.get_absolute_url()
        ban_cmd = ban_path % {'url': url, 'host': settings.MAIN_HOSTNAME}
        manager = VarnishManager(settings.VARNISH_MANAGEMENT_SERVERS)
        manager.run('ban', ban_cmd, secret=settings.VARNISH_SECRET)

    set_urlconf(current_urlconf)

def django_invalidate_page(p):
    def _do_invalidate():
        key = PageDetailView.get_cache_key(slug=p.slug, region=p.region.slug)
        cache.delete(key)

    from pages.views import PageDetailView

    current_urlconf = get_urlconf()

    if p.region.regionsettings.domain:
        # Has a domain, ugh. Need to clear two URLs on two hosts, in this case
        set_urlconf('main.urls_no_region')

        _do_invalidate()

        # Now invalidate main path on LocalWiki hub
        set_urlconf('main.urls')
    _do_invalidate()

    set_urlconf(current_urlconf)

@shared_task(ignore_result=True)
def _async_cache_post_edit(instance, created=False, deleted=False, raw=False):
    from pages.models import Page
    from maps.models import MapData
    from tags.models import PageTagSet
    from links.models import Link, IncludedPage

    if isinstance(instance, Page):
        # First, let's clear out the Varnish cache for this page
        varnish_invalidate_page(instance)

        # Then we clear the cache for pages that depend on this page
        if created or deleted:
            # Clear the cache for pages that link to this page, as the
            # link dashed-underline-status has changed.
            for p in instance.links_to_here.all():
                varnish_invalidate_page(p.source)
                django_invalidate_page(p.source)

        # Clear out the cache for pages that include this page
        for p in instance.pages_that_include_this.all():
            varnish_invalidate_page(p.source)
            django_invalidate_page(p.source)

    elif isinstance(instance, MapData):
        varnish_invalidate_page(instance.page)
    elif isinstance(instance, PageTagSet):
        varnish_invalidate_page(instance.page)

def _page_cache_post_edit(sender, instance, created=False, deleted=False, raw=False, **kwargs):
    # We want to syncronously clear the page cache when it's been edited directly, or an
    # embedded object has been edited directly.  This is so a user who's just edited the page
    # (or tags, or map, etc) will see the update immediately.
    #
    # We process varnish invalidation and other dependent object invalidation in an async task.

    from pages.models import Page
    from maps.models import MapData
    from tags.models import PageTagSet
    from links.models import Link, IncludedPage

    if isinstance(instance, Page):
        django_invalidate_page(instance)
    elif isinstance(instance, MapData):
        django_invalidate_page(p.source)
    elif isinstance(instance, PageTagSet):
        django_invalidate_page(p.source)

    _async_cache_post_edit(instance, created=created, deleted=deleted, raw=raw)

def _page_cache_post_save(sender, instance, created, raw, **kwargs):
    _page_cache_post_edit(sender, instance, created=created, deleted=False, raw=raw, **kwargs)

def _page_cache_post_delete(sender, instance, **kwargs):
    _page_cache_post_edit(sender, instance, deleted=True, **kwargs)
