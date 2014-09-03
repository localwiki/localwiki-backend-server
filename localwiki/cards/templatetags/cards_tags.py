import copy

from django import template
from django.core.cache import get_cache
from django.conf import settings
from django.template.loader import render_to_string
from django.db.models.signals import post_save
from django.core.urlresolvers import get_urlconf

from regions.models import Region
from pages.models import Page
from frontpage.models import FrontPage
from maps.widgets import InfoMap

register = template.Library()

# Remove the PanZoom on normal page views.
olwidget_options = copy.deepcopy(getattr(settings,
    'OLWIDGET_DEFAULT_OPTIONS', {}))
map_opts = olwidget_options.get('map_options', {})
map_controls = map_opts.get('controls', [])
if 'PanZoom' in map_controls:
    map_controls.remove('PanZoom')
if 'PanZoomBar' in map_controls:
    map_controls.remove('PanZoomBar')
if 'KeyboardDefaults' in map_controls:
    map_controls.remove('KeyboardDefaults')
if 'Navigation' in map_controls:
    map_controls.remove('Navigation')

olwidget_options['map_options'] = map_opts
olwidget_options['map_div_class'] = 'mapwidget'


@register.simple_tag(takes_context=True)
def show_card(context, obj):
    if isinstance(obj, Page):
        return render_page_card(context, obj)
    elif isinstance(obj, Region):
        return render_region_card(context, obj)


def render_page_card(context, page):
    from maps.widgets import map_options_for_region
    cache = get_cache('long-living')
    request = context['request']

    card = cache.get('card:%s,%s' % (get_urlconf(), page.id))
    if card:
        return card

    _file, _map = None, None

    # Try and get a useful image
    _file = page.get_highlight_image() 

    # Otherwise, try and get a map
    if not _file and hasattr(page, 'mapdata'):
        olwidget_options.update(map_options_for_region(page.region))
        _map = InfoMap(
            [(page.mapdata.geom, '')],
            options=olwidget_options
        ).render(None, None, {'id': 'map_page_id_%s' % page.id})

    card = render_to_string('cards/base.html', {
        'obj': page,
        'file': _file.file if _file else None,
        'map': _map,
        'title': page.name,
        'content': page.content,
    })

    cache.set('card:%s,%s' % (get_urlconf(), page.id), card)
    return card


def render_region_card(context, region):
    from maps.widgets import map_options_for_region
    cache = get_cache('long-living')
    request = context['request']

    card = cache.get('rcard:%s' % region.id)
    if card:
        return card

    _file, _map, front_page_content = None, None, None
    is_meta_region = hasattr(region, 'regionsettings') and region.regionsettings.is_meta_region

    if Page.objects.filter(region=region, slug='front page'):
        front_page_content = Page.objects.get(region=region, slug='front page').content

    # User the cover photo, if it exists, as the thumbnail
    if FrontPage.objects.filter(region=region).exists():
        frontpage = FrontPage.objects.get(region=region)
        if frontpage.cover_photo:
            _file = frontpage.cover_photo

    # Otherwise, try and get a map
    if not _file and not is_meta_region and region.geom:
        map_opts = map_options_for_region(region)
        map_opts['default_zoom'] -= 1
        olwidget_options.update(map_opts)
        _map = InfoMap(
            [(None, '')],
            options=olwidget_options
        ).render(None, None, {'id': 'map_region_id_%s' % region.id})

    card = render_to_string('cards/base.html', {
        'obj': region,
        'file': _file,
        'map': _map,
        'title': region.full_name,
        'content': front_page_content,
    })
    cache.set('rcard:%s' % region.id, card)
    return card

    
def _clear_page_card(sender, instance, *args, **kwargs):
    cache = get_cache('long-living')
    if instance.region.regionsettings.domain:
        # Have to clear both urlconfs
        cache.delete('card:main.urls_no_region,%s' % instance.id)
    cache.delete('card:main.urls,%s' % instance.id)

post_save.connect(_clear_page_card, sender=Page)
