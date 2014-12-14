from celery import shared_task
from lxml.html import fragments_fromstring
import urllib
import urlparse

from django.utils.translation import ugettext as _
from django.utils.encoding import smart_str
from django.db import models
from django.db.models import Avg
from django.core.cache import cache
from django.db.models.signals import post_save

from pages.models import Page, slugify
from links.models import Link

SKIP_USER_PAGES_FOR_PAGESCORE = True


class PageScore(models.Model):
    """
    A score assigned to a page that, roughly speaking, represents its
    quality.
    """
    page = models.OneToOneField(Page, related_name='score')
    score = models.SmallIntegerField()
    page_content_length = models.PositiveIntegerField()  # Needed for some score metrics

    def __unicode__(self):
        return _("Page score %s: %s") % (self.page, self.score)


def is_internal(url):
    return (not urlparse.urlparse(url).netloc)

def is_plugin(elem):
    classes = elem.attrib.get('class', '')
    return ('plugin' in classes.split())

def avg_incoming_links_for_region(region):    
    avg = cache.get('avg_incoming_links:%s' % region.slug)
    if avg is not None:
        return avg

    # XXX TODO remove this once all
    # /User/ pages are moved to a single global namespace
    if SKIP_USER_PAGES_FOR_PAGESCORE:
        num_pages = Page.objects.filter(region=region).exclude(slug__startswith='users/').count()
    else:
        num_pages = Page.objects.filter(region=region).count()

    num_links = Link.objects.filter(region=region).count()
    if num_links:
        avg = (num_links * 1.0) / num_pages
    else:
        avg = 0

    cache.set('avg_incoming_links:%s' % region.slug, avg, 60 * 15)
    return avg

def avg_page_length(region):    
    avg = cache.get('avg_page_length:%s' % region.slug)
    if avg is not None:
        return avg

    qs = Page.objects.filter(region=region)
    # XXX TODO remove this once all
    # /User/ pages are moved to a single global namespace
    if SKIP_USER_PAGES_FOR_PAGESCORE:
        qs = qs.exclude(slug__istartswith='users/')

    avg = qs.aggregate(avg=Avg('score__page_content_length'))['avg']

    cache.set('avg_page_length:%s' % region.slug, avg, 60 * 15)
    return avg

def _compute_score(page):
    from maps.models import MapData
    from pages.plugins import _files_url

    score = 0
    num_images = 0
    link_num = 0

    # XXX TODO remove this once all
    # /User/ pages are moved to a single global namespace
    if SKIP_USER_PAGES_FOR_PAGESCORE:
        if page.slug.startswith('users/'):
            return 0

    # 1 point for having a map
    if MapData.objects.filter(page=page).exists():
        score += 1

    # Parse the page HTML and look for good stuff
    for e in fragments_fromstring(page.content):
        if isinstance(e, basestring):
            continue
        for i in e.iter('img'):
            src = i.attrib.get('src', '')
            if src.startswith(_files_url):
                num_images += 1
        for i in e.iter('a'):
            src = i.attrib.get('href', '')
            if is_internal(src) and not is_plugin(i):
                slug = slugify(unicode(urllib.unquote(src), 'utf-8', errors='ignore'))
                # Only count links to pages that exist
                if Page.objects.filter(slug=slug, region=page.region).exists():
                    link_num += 1

    # One point for each image, up to three points
    score += min(num_images, 3)

    # 1 point for the first internal link and 1 point if there's at least
    # two more links.
    if link_num >= 1:
        score += 1
    if link_num >= 3:
        score += 1

    # 1 point for a page length >= average page length
    avg_page_length = Page.objects.filter(region=page.region).aggregate(
        avg=Avg('score__page_content_length'))
    if len(page.content) >= avg_page_length:
        score += min(int((len(page.content) * 1.0) / avg_page_length), 3)

    # Use # of incoming links in the page score
    avg_links_to = avg_incoming_links_for_region(page.region)
    num_links_to_here = page.links_to_here.count()
    if num_links_to_here >= avg_links_to:
        score += min(int((num_links_to_here * 1.0) / avg_links_to), 5)

    # Normalize to get more randomness.  Otherwise we'd see the top few pages all the time on Explore
    score = min(score, 8)

    return score

@shared_task(ignore_result=True)
def _calculate_page_score(page_id):
    page = Page.objects.filter(id=page_id)
    if page.exists():
        page = page[0]
    else:
        return

    score = _compute_score(page)
    
    score_obj = PageScore.objects.filter(page=page)
    if not score_obj.exists():
        score_obj = PageScore(page=page)
    else:
        score_obj = score_obj[0]
    score_obj.score = score
    score_obj.page_content_length = len(page.content)
    score_obj.save()

def _handle_page_score(sender, instance, created, raw, **kws):
    from maps.models import MapData

    if raw:
        return
    if sender == Page:
        if getattr(instance, '_in_rename', False):
            return

        _calculate_page_score.delay(instance.id)
    elif sender == MapData:
        _calculate_page_score.delay(instance.page.id)


post_save.connect(_handle_page_score)
