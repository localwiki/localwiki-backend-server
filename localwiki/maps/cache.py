from django.core.cache import cache
from django.core.urlresolvers import set_urlconf, get_urlconf

from celery import shared_task

from regions.models import Region


@shared_task(ignore_result=True)
def django_invalidate_region_map(region_id):
    region = Region.objects.get(id=region_id)

    def _do_invalidate():
        key = MapFullRegionView.get_cache_key(region=region.slug)
        cache.delete(key)

    from maps.views import MapFullRegionView

    current_urlconf = get_urlconf() or settings.ROOT_URLCONF

    if region.regionsettings.domain:
        # Has a domain, ugh. Need to clear two URLs on two hosts, in this case
        set_urlconf('main.urls_no_region')

        _do_invalidate()

        # Now invalidate main path on LocalWiki hub
        set_urlconf('main.urls')
    _do_invalidate()

    set_urlconf(current_urlconf)

def _map_cache_post_edit(sender, instance, **kwargs):
    django_invalidate_region_map(instance.region.id)

def _map_cache_post_save(sender, instance, created, raw, **kwargs):
    _map_cache_post_edit(sender, instance, **kwargs)

def _map_cache_pre_delete(sender, instance, **kwargs):
    _map_cache_post_edit(sender, instance, **kwargs)
