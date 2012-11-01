from tags.views import PageNotFoundMixin
from utils.views import PermissionRequiredMixin, CreateObjectMixin
from versionutils.versioning.views import UpdateView, VersionsList
from infobox.forms import InfoboxForm
from pages.models import Page
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.views.generic.list import ListView
from forms import AttributeCreateForm, AttributeUpdateForm, AddAttributeForm
from django.views.generic.edit import CreateView
from models import PageAttribute, PageValue

class InfoboxUpdateView(PageNotFoundMixin, PermissionRequiredMixin,
        CreateObjectMixin, UpdateView):
    form_class = InfoboxForm
    permission = 'pages.change_page'

    def get_object(self):
        page_slug = self.kwargs.get('slug')
        return get_object_or_404(Page, slug=page_slug)

    def get_success_url(self):
        next = self.request.POST.get('next', None)
        if next:
            return next
        return reverse('pages:infobox', args=[self.kwargs.get('slug')])

    def get_protected_object(self):
        return self.object


class InfoboxAddAttributeView(PageNotFoundMixin, PermissionRequiredMixin,
                              UpdateView):
    form_class = AddAttributeForm
    permission = 'pages.change_page'

    def get_object(self):
        page_slug = self.kwargs.get('slug')
        return get_object_or_404(Page, slug=page_slug)

    def get_success_url(self):
        next = self.request.POST.get('next', None)
        if next:
            return next
        return reverse('pages:infobox', args=[self.kwargs.get('slug')])

    def get_protected_object(self):
        return self.object


class AttributeListView(ListView):
    context_object_name = 'attribute_list'
    template_name = 'infobox/attribute_list.html'

    def get_queryset(self):
        return PageAttribute.get_for_model(Page)


class AttributeUpdateView(UpdateView):
    model = PageAttribute
    form_class = AttributeUpdateForm
    context_object_name = 'attribute'
    template_name = 'infobox/attribute_form.html'

    def get_success_url(self):
        return reverse('infobox:attribute-list')


class AttributeCreateView(CreateView):
    model = PageAttribute
    form_class = AttributeCreateForm
    context_object_name = 'attribute'
    template_name = 'infobox/attribute_form.html'

    def get_success_url(self):
        return reverse('infobox:attribute-list')


class InfoboxVersions(VersionsList):
    def get_queryset(self):
        page_slug = self.kwargs.get('slug')
        try:
            self.page = get_object_or_404(Page, slug=page_slug)
            # Page is versioned, so we have to do a join query
            return PageValue.versions.filter(entity__id=self.page.id)
        except PageValue.DoesNotExist:
            return PageValue.versions.none()

    def get_context_data(self, **kwargs):
        context = super(InfoboxVersions, self).get_context_data(**kwargs)
        context['page'] = self.page
        return context
    