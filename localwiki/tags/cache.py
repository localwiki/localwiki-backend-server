from django.core.urlresolvers import set_urlconf, get_urlconf
from django.conf import settings
from django.core.cache import cache

from localwiki.utils.urlresolvers import reverse


def varnish_invalidate_tag_view(slug, region):
    from pages.cache import varnish_invalidate_url

    current_urlconf = get_urlconf() or settings.ROOT_URLCONF

    if region.regionsettings.domain:
        # Has a domain, ugh. Need to clear two URLs on two hosts, in this case
        set_urlconf('main.urls_no_region')
        url = reverse('tags:tagged', kwargs={'slug': slug, 'region': region.slug})
        varnish_invalidate_url(url, hostname=region.regionsettings.domain)

        # Now invalidate main path on LocalWiki hub
        set_urlconf('main.urls')
        url = reverse('tags:tagged', kwargs={'slug': slug, 'region': region.slug})
        varnish_invalidate_url(url)
    else:
        url = reverse('tags:tagged', kwargs={'slug': slug, 'region': region.slug})
        varnish_invalidate_url(url)

    set_urlconf(current_urlconf)

def django_invalidate_tag_view(slug, region):
    def _do_invalidate():
        key = TaggedList.get_cache_key(slug=slug, region=region.slug)
        cache.delete(key)

    from tags.views import TaggedList

    current_urlconf = get_urlconf() or settings.ROOT_URLCONF

    if region.regionsettings.domain:
        # Has a domain, ugh. Need to clear two URLs on two hosts, in this case
        set_urlconf('main.urls_no_region')

        _do_invalidate()

        # Now invalidate main path on LocalWiki hub
        set_urlconf('main.urls')
    _do_invalidate()

    set_urlconf(current_urlconf)

def varnish_invalidate_global_tag_view(slug):
    from pages.cache import varnish_invalidate_url

    url = reverse('tags:global-tagged', kwargs={'slug': slug})
    varnish_invalidate_url(url)

def django_invalidate_global_tag_view(slug):
    from tags.views import GlobalTaggedList

    key = GlobalTaggedList.get_cache_key(slug=slug)
    cache.delete(key)
