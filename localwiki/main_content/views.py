from django.views.generic import View
from django.utils.translation import get_language

from regions.models import Region
from regions.views import RegionListView
from blog.models import Post


class SplashPageView(RegionListView):
    template_name = "main_content/index.html"
    zoom_to_data = False

    def get_context_data(self, *args, **kwargs):
        context = super(SplashPageView, self).get_context_data(*args, **kwargs)

        qs = Region.objects.exclude(regionsettings__is_meta_region=True)
        qs = qs.exclude(is_active=False)

        # Exclude ones with empty scores
        qs = qs.exclude(score=None)

        qs = qs.order_by('-score__score', '?')

        ## Just grab 5 items
        qs = qs[:5]

        context['regions_for_cards'] = qs
        context['blogs'] = Post.objects.filter(status=2).order_by('-created')[:4]
        language_main = 'main-%s' % get_language()
        if Region.objects.filter(slug=language_main).exists():
            context['main_url'] = Region.objects.get(slug=language_main).get_absolute_url()
        return context


class MainPageView(View):
    def get(self, request):
        from activity.views import FollowedActivity

        if request.user.is_authenticated():
            view_func = FollowedActivity.as_view()
        else:
            view_func = SplashPageView.as_view()
        return view_func(request)
