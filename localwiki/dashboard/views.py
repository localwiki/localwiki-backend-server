from datetime import date, datetime, timedelta

from django.core.cache import cache
from django.contrib.auth.models import User
from django.db.models import Max
from django.utils.translation import ugettext as _

import pyflot
import qsstats

from pages.models import Page, PageFile
from regions.models import Region
from regions.views import RegionMixin, TemplateView
from maps.models import MapData
from redirects.models import Redirect
from utils.views import JSONView

from versionutils.versioning.constants import *

import time

COMPLETE_CACHE_TIME = 60 * 60 * 5
EASIER_CACHE_TIME = 60  # cache easier stuff for 60 seconds.


class DashboardView(TemplateView):
    template_name = 'dashboard/index.html'


class DashboardRenderView(RegionMixin, JSONView):
    def get_nums(self):
        region = self.get_region()
        nums = cache.get('region:%s:dashboard_nums' % region.slug)
        if nums is None:
            nums = {
                'num_pages': Page.objects.filter(region=region).count(),
                'num_files': PageFile.objects.filter(region=region).count(),
                'num_maps': MapData.objects.filter(region=region).count(),
                'num_redirects': Redirect.objects.filter(region=region).count(),
                'num_users': User.objects.count()
            }
            cache.set('region:%s:dashboard_nums' % region.slug, nums,
                EASIER_CACHE_TIME)
            nums['_regenerated_nums'] = True
        nums['generated'] = True
        return nums

    def get_oldest_page_date(self):
        region = self.get_region()
        oldest = cache.get('region:%s:dashboard_oldest' % region.slug)
        if oldest is None:
            qs = Page.versions.filter(region=region).order_by('history_date')
            qs = qs.filter(history_date__gte=date(2000, 1, 1))
            if not qs.exists():
                return None
            oldest = qs[0].version_info.date
            cache.set('region:%s:dashboard_oldest' % region.slug, oldest, COMPLETE_CACHE_TIME)
        return oldest

    def get_context_data_for_chart(self, function, key):
        region = self.get_region()
        context = cache.get('region:%s:dashboard_%s' % (region.slug, key))

        if context is not None:
            context['_cached'] = True
            context['_age'] = time.time() - context['_built']
            context['generated'] = True
            return context

        start_at = time.time()
        oldest = self.get_oldest_page_date()

        if oldest is None:
            # We probably have no pages yet
            return {'generated': True, key: [], '_error': 'No page data'}

        if 'check_cache' in self.request.GET or cache.get('region:%s:dashboard_generating_%s' % (region.slug, key), False):
            return {'generated': False}

        cache.set('region:%s:dashboard_generating_%s' % (region.slug, key), True, 60)

        context = {}
        context[key] = function(oldest, region)

        context['_built'] = time.time()
        context['_duration'] = time.time() - start_at
        context['generated'] = True
        cache.set('region:%s:dashboard_%s' % (region.slug, key), context, COMPLETE_CACHE_TIME)
        cache.set('region:%s:dashboard_generating_%s' % (region.slug, key), False)

        context['_age'] = time.time() - context['_built']
        context['_cached'] = False

        return context

    def get_context_data(self, *args, **kwargs):
        if 'graph' in self.request.GET:
            if self.request.GET.get('graph', None) == 'num_items_over_time':
                return self.get_context_data_for_chart(items_over_time, 'num_items_over_time')
            elif self.request.GET.get('graph', None) == 'num_edits_over_time':
                return self.get_context_data_for_chart(edits_over_time, 'num_edits_over_time')
            elif self.request.GET.get('graph', None) == 'users_registered_over_time':
                return self.get_context_data_for_chart(users_registered_over_time, 'users_registered_over_time')
            elif self.request.GET.get('graph', None) == 'page_content_over_time':
                return self.get_context_data_for_chart(page_content_over_time, 'page_content_over_time')

        return self.get_nums()


def _summed_series(series):
    """
    Take a time series, ``series``, and turn it into a summed-by-term series.
    """
    sum = 0
    l = []
    for (d, num) in series:
        sum += num
        l.append((d, sum))
    return l


def _sum_from_add_del(added_series, deleted_series):
    """
    Sum the provided, aligned time series (added, deleted).
    """
    sum = 0
    l = []
    for ((d, added), (_, deleted)) in zip(added_series, deleted_series):
        sum += (added - deleted)
        l.append((d, sum))
    return l


def items_over_time(oldest_page, region):
    graph = pyflot.Flot()

    pages_added = qsstats.QuerySetStats(
        Page.versions.filter(region=region, version_info__type__in=ADDED_TYPES),
        'history_date').time_series(oldest_page)
    pages_deleted = qsstats.QuerySetStats(
        Page.versions.filter(region=region, version_info__type__in=DELETED_TYPES),
        'history_date').time_series(oldest_page)
    num_pages_over_time = _sum_from_add_del(pages_added, pages_deleted)

    maps_added = qsstats.QuerySetStats(
        MapData.versions.filter(region=region, version_info__type__in=ADDED_TYPES),
        'history_date').time_series(oldest_page)
    maps_deleted = qsstats.QuerySetStats(
        MapData.versions.filter(region=region, version_info__type__in=DELETED_TYPES),
        'history_date').time_series(oldest_page)
    num_maps_over_time = _sum_from_add_del(maps_added, maps_deleted)

    files_added = qsstats.QuerySetStats(
        PageFile.versions.filter(region=region, version_info__type__in=ADDED_TYPES),
        'history_date').time_series(oldest_page)
    files_deleted = qsstats.QuerySetStats(
        PageFile.versions.filter(region=region, version_info__type__in=DELETED_TYPES),
        'history_date').time_series(oldest_page)
    num_files_over_time = _sum_from_add_del(files_added, files_deleted)

    redir_added = qsstats.QuerySetStats(
        Redirect.versions.filter(region=region, version_info__type__in=ADDED_TYPES),
        'history_date').time_series(oldest_page)
    redir_deleted = qsstats.QuerySetStats(
        Redirect.versions.filter(region=region, version_info__type__in=DELETED_TYPES),
        'history_date').time_series(oldest_page)
    num_redirects_over_time = _sum_from_add_del(redir_added, redir_deleted)

    graph.add_time_series(num_pages_over_time, label=_("pages"))
    graph.add_time_series(num_maps_over_time, label=_("maps"))
    graph.add_time_series(num_files_over_time, label=_("files"))
    graph.add_time_series(num_redirects_over_time,
        label=_("redirects"))

    return [graph.prepare_series(s) for s in graph._series]


def edits_over_time(oldest_page, region):
    graph = pyflot.Flot()

    qss = qsstats.QuerySetStats(Page.versions.filter(region=region), 'history_date')
    graph.add_time_series(qss.time_series(oldest_page), label=_("pages"))

    qss = qsstats.QuerySetStats(MapData.versions.filter(region=region), 'history_date')
    graph.add_time_series(qss.time_series(oldest_page), label=_("maps"))

    qss = qsstats.QuerySetStats(PageFile.versions.filter(region=region), 'history_date')
    graph.add_time_series(qss.time_series(oldest_page), label=_("files"))

    qss = qsstats.QuerySetStats(Redirect.versions.filter(region=region), 'history_date')
    graph.add_time_series(qss.time_series(oldest_page), label=_("redirects"))

    return [graph.prepare_series(s) for s in graph._series]


def page_content_over_time(oldest_page, region):
    qs = Page.versions.filter(region=region).extra(
        {'content_length': "length(content)",
         'history_day': "date(history_date)"})
    qs = qs.order_by('history_day')
    qs = qs.values('content_length', 'history_day', 'slug')

    graph = pyflot.Flot()
    page_dict = {}
    page_contents = []
    current_day = oldest_page.date()

    for page in qs.iterator():
        print 'page', page
        if page['history_day'] > current_day:
            page_contents.append((current_day, sum(page_dict.values())))
            current_day = page['history_day']
        page_dict[page['slug']] = page['content_length']

    graph.add_time_series(page_contents)
    return [graph.prepare_series(s) for s in graph._series]


def users_registered_over_time(oldest_page, region):
    oldest_user = User.objects.order_by('date_joined')[0].date_joined
    graph = pyflot.Flot()

    qss = qsstats.QuerySetStats(User.objects.all(), 'date_joined')
    graph.add_time_series(_summed_series(qss.time_series(oldest_user)))

    return [graph.prepare_series(s) for s in graph._series]
