import urllib

from django.conf import settings
from django.core.urlresolvers import set_urlconf, get_urlconf
from django.core.cache import cache

from celery import shared_task
from varnish import VarnishManager

rfc_3986_reserved = """!*'();:@&=+$,/?#[]"""
rfc_3986_unreserved = """ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_.~"""
VARNISH_SAFE = rfc_3986_reserved + rfc_3986_unreserved


def varnish_invalidate_url(url, hostname=None):
    if not hostname:
        hostname = settings.MAIN_HOSTNAME

    ban_path = r'obj.http.x-url ~ ^(?i)(%(url)s(/*)(\\?.*)?)$ && obj.http.x-host ~ ^((?i)(.*\\.)?%(host)s(:[0-9]*)?)$'

    # Varnish needs it quoted, but has a wonky way of encoding URLs :/
    url = urllib.unquote(url)
    url = urllib.quote(url, safe=VARNISH_SAFE)
    if type(url) != unicode:
        url = url.decode('utf-8')
    ban_cmd = (ban_path % {'url': url, 'host': hostname}).encode('utf-8')
    manager = VarnishManager(settings.VARNISH_MANAGEMENT_SERVERS)
    manager.run('ban', ban_cmd, secret=settings.VARNISH_SECRET)

def varnish_invalidate_page(p):
    current_urlconf = get_urlconf() or settings.ROOT_URLCONF

    if p.region.regionsettings.domain:
        # Has a domain, ugh. Need to clear two URLs on two hosts, in this case
        set_urlconf('main.urls_no_region')
        varnish_invalidate_url(p.get_absolute_url(), hostname=p.region.regionsettings.domain)

        # Now invalidate main path on LocalWiki hub
        set_urlconf('main.urls')
        varnish_invalidate_url(p.get_absolute_url())
    else:
        varnish_invalidate_url(p.get_absolute_url())

    set_urlconf(current_urlconf)

def django_invalidate_page(p):
    def _do_invalidate():
        key = PageDetailView.get_cache_key(slug=p.slug, region=p.region.slug)
        cache.delete(key)

    from pages.views import PageDetailView

    current_urlconf = get_urlconf() or settings.ROOT_URLCONF

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
    from links.models import Link, IncludedPage, IncludedTagList
    from tags.cache import django_invalidate_tag_view, varnish_invalidate_tag_view

    if isinstance(instance, Page):
        # First, let's clear out the Varnish cache for this page
        varnish_invalidate_page(instance)

        # Then we clear the cache for pages that depend on this page
        if created or deleted:
            # Clear the cache for pages that link to this page, as the
            # link dashed-underline-status has changed.

            # First, make sure and get all the page links, whether or not the
            # destination page exists:
            links_to_here = set([l.source for l in instance.links_to_here.all()])
            other_links = Link.objects.filter(destination_name__iexact=instance.slug)
            other_links = [Page(name=l.source.name, slug=l.source.slug, region=instance.region) for l in other_links]
            links_to_here = set.union(links_to_here, other_links)

            for p in links_to_here:
                varnish_invalidate_page(p)
                django_invalidate_page(p)

        # Clear out the cache for pages that include this page
        for p in instance.pages_that_include_this.all():
            varnish_invalidate_page(p.source)
            django_invalidate_page(p.source)

    elif isinstance(instance, MapData):
        varnish_invalidate_page(instance.page)

    # Only ever deal with PageTagSet if deleted (otherwise we deal with m2m_changed)
    elif isinstance(instance, PageTagSet) and deleted:
        varnish_invalidate_page(instance.page)
        django_invalidate_page(instance.page)

        # Clear tag list views
        for slug in changed:
            varnish_invalidate_tag_view(slug, instance.region)
            django_invalidate_tag_view(slug, instance.region)

        # Clear out the pages that include a 'list of tagged pages' of the deleted
        # tags:
        slugs_before_delete = [t.slug for t in instance.versions.all()[1].tags.all()]
        for tl in IncludedTagList.objects.filter(included_tag__slug__in=slugs_before_delete):
            varnish_invalidate_page(tl.source)
            django_invalidate_page(tl.source)

def _page_cache_post_edit(sender, instance, created=False, deleted=False, raw=False, **kwargs):
    # We want to syncronously clear the page cache when it's been edited directly, or an
    # embedded object has been edited directly.  This is so a user who's just edited the page
    # (or tags, or map, etc) will see the update immediately.
    #
    # We process varnish invalidation and other dependent object invalidation in an async task.

    from pages.models import Page
    from maps.models import MapData
    from tags.models import PageTagSet

    if isinstance(instance, Page):
        django_invalidate_page(instance)
    elif isinstance(instance, MapData):
        django_invalidate_page(instance.page)
    elif isinstance(instance, PageTagSet):
        django_invalidate_page(instance.page)

    _async_cache_post_edit.delay(instance, created=created, deleted=deleted, raw=raw)

@shared_task(ignore_result=True)
def _async_pagetagset_m2m_changed(instance):
    from links.models import IncludedTagList
    from versionutils.diff import diff
    from tags.cache import django_invalidate_tag_view, varnish_invalidate_tag_view

    varnish_invalidate_page(instance.page)
    django_invalidate_page(instance.page)

    # This seems roundabout because it is. We clear() out the tag set each time
    # the PageTagSet is changed[1], so we have to check what's changed in this
    # roundabout manner.
    #
    # 1. Not sure why, but may be worth looking into.

    if instance.versions.all().count() == 1:
        changed = [t.slug for t in instance.tags.all()]
    else:
        # Most recent two versions
        v2, v1 = instance.versions.all()[:2]
        items = diff(v1, v2).get_diff()['tags'].get_diff()
        changed = [t.slug for t in set.union(items['added'], items['deleted'])]

    # Clear tag list views
    for slug in changed:
        varnish_invalidate_tag_view(slug, instance.region)
        django_invalidate_tag_view(slug, instance.region)

    # Clear caches of pages that include these tags as "list of tagged pages"
    for tl in IncludedTagList.objects.filter(included_tag__slug__in=changed):
        varnish_invalidate_page(tl.source)
        django_invalidate_page(tl.source)

def _page_cache_post_save(sender, instance, created, raw, **kwargs):
    _page_cache_post_edit(sender, instance, created=created, deleted=False, raw=raw, **kwargs)

def _page_cache_pre_delete(sender, instance, **kwargs):
    _page_cache_post_edit(sender, instance, deleted=True, **kwargs)

def _pagetagset_m2m_changed(sender, instance, action, reverse, model, pk_set, *args, **kwargs):
    if action == 'post_clear' and not pk_set:
        # No information, so skip this.
        return

    if action == 'post_add' or action == 'post_remove' or action == 'post_clear':
        # Get the tags in this transaction before handing off to celery
        instance.tags.all()
        _async_pagetagset_m2m_changed.delay(instance)
