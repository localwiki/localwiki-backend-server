from django.views.generic import TemplateView

from regions.views import RegionMixin
from pages.models import Page, slugify

from .models import Link


class LinksForPageView(RegionMixin, TemplateView):
    template_name = 'links/links_for_page.html'

    def get_context_data(self, *args, **kwargs):
        context = super(LinksForPageView, self) .get_context_data(*args, **kwargs)
        page = Page.objects.get(
            slug=slugify(self.kwargs.get('slug')),
            region=self.get_region()
        )
        context['page'] = page
        context['links_to_page'] = page.links_to_here.all()
        context['links_from_page'] = page.links.all()
        return context


class OrphanedPagesView(RegionMixin, TemplateView):
    template_name = 'links/orphaned_pages.html'

    def get_context_data(self, *args, **kwargs):
        context = super(OrphanedPagesView, self) .get_context_data(*args, **kwargs)
        return context
