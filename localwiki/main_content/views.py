from django.views.generic import View

from pages.models import Page
from regions.views import RegionListView


class SplashPageView(RegionListView):
    template_name = "main_content/index.html"
    zoom_to_data = False

    def get_context_data(self, *args, **kwargs):
        context = super(SplashPageView, self).get_context_data(*args, **kwargs)

        # Exclude meta stuff
        qs = Page.objects.all()
        qs = qs.exclude(slug__startswith='templates/')
        qs = qs.exclude(slug='templates')
        qs = qs.exclude(slug='front page')

        # Exclude ones with empty scores
        qs = qs.exclude(score=None)

        qs = qs.defer('content').select_related('region').order_by('-score__score', '?')

        # Just grab 5 items
        qs = qs[:5]

        context['pages_for_cards'] = qs
        return context


class MainPageView(View):
    def get(self, request):
        from activity.views import FollowedActivity

        if request.user.is_authenticated():
            view_func = FollowedActivity.as_view()
        else:
            view_func = SplashPageView.as_view()
        return view_func(request)
