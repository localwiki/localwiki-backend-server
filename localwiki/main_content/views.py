from django.views.generic import View
from django.utils.translation import get_language
from django.db.models import Q

from localwiki.utils.models import MultiQuerySet
from regions.models import Region
from regions.views import RegionListView
from blog.models import Post


class SplashPageView(RegionListView):
    template_name = "main_content/index.html"
    zoom_to_data = False

    def get_context_data(self, *args, **kwargs):
        from pages.models import Page
        from regions.models import Region

        context = super(SplashPageView, self).get_context_data(*args, **kwargs)

        qs = Region.objects.exclude(regionsettings__is_meta_region=True)
        qs = qs.exclude(is_active=False)

        # Exclude ones with empty scores
        qs = qs.exclude(score=None)

        qs = qs.order_by('-score__score', '?')

        # First, all results in their language, then all other results following their language's results:
        language = get_language()
        if language == 'en':
            qs_our_language = qs.filter(
                Q(regionsettings__default_language=language) | Q(regionsettings__default_language__isnull=True)
            )
        else:
            qs_our_language = qs.filter(regionsettings__default_language=language)
        qs_rest = qs.exclude(regionsettings__default_language=language)
        qs = MultiQuerySet(qs_our_language, qs_rest)

        ## Just grab 5 items
        qs = qs[:5]

        context['regions_for_cards'] = qs
        context['blogs'] = Post.objects.filter(status=2).order_by('-created')[:4]

        context['page_count'] = (Page.objects.all().count() // 1000) * 1000
        context['region_count'] = Region.objects.all().count()
        context['countries_count'] = 15
        context['languages_count'] = 7
        return context

    def get_map_options(self):
        olwidget_options = super(SplashPageView, self).get_map_options()
        map_opts = olwidget_options.get('map_options', {})
        map_opts['controls'] = []
        olwidget_options['overlay_style'] = {
            'strokeDashstyle': 'solid',
            'strokeColor': '#444',
            'strokeOpacity': 0.2,
            'fillOpacity': 1,
            'fillColor': '#eA3',
            'strokeWidth': 0.5,
            'pointRadius': 2
        }
        olwidget_options['default_zoom'] = 1
        return olwidget_options


class MainPageView(View):
    def get(self, request):
        from activity.views import FollowedActivity

        if request.user.is_authenticated():
            view_func = FollowedActivity.as_view()
        else:
            view_func = SplashPageView.as_view()
        return view_func(request)
