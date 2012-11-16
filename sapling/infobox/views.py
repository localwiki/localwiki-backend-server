from tags.views import PageNotFoundMixin
from utils.views import PermissionRequiredMixin, CreateObjectMixin
from versionutils.versioning.views import UpdateView, VersionsList
from versionutils.diff.views import CompareView
from infobox.forms import InfoboxForm
from pages.models import Page
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.views.generic.list import ListView
from forms import AttributeCreateForm, AttributeUpdateForm, AddAttributeForm
from django.views.generic.edit import CreateView
from models import PageAttribute, PageValue, EntityAsOf
from templatetags.infobox_tags import render_attribute
from django.views.generic.detail import DetailView
from eav.models import Entity


class InfoboxUpdateView(PageNotFoundMixin, PermissionRequiredMixin,
        CreateObjectMixin, UpdateView):
    form_class = InfoboxForm
    permission = 'pages.change_page'
    template_name = 'infobox/infobox_detail.html'

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
    template_name = 'infobox/infobox_versions.html'

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


class InfoboxVersionDetailView(DetailView):
    context_object_name = 'infobox'

    template_name = 'infobox/infobox_version_detail.html'

    def get_object(self):
        page_slug = self.kwargs.get('slug')
        try:
            self.page = Page.objects.get(slug=page_slug)
            version = self.kwargs.get('version')
            date = self.kwargs.get('date')
            return EntityAsOf(self.page, date=date, version=version)
        except (Page.DoesNotExist, IndexError):
            return None

    def get_context_data(self, **kwargs):
        context = super(InfoboxVersionDetailView,
                        self).get_context_data(**kwargs)
        context['page'] = self.page
        context['show_revision'] = True
        attributes = []
        infobox_dict = context['infobox'].eav_attributes
        for a in PageAttribute.objects.all():
            if a.slug in infobox_dict:
                value_version = infobox_dict[a.slug]
                # value is a property, not accessible through the historical
                # instance, so we have to derive it again
                value = getattr(value_version, 'value_%s' % a.datatype)
                attributes.append({ 'name': a.name,
                                    'html': render_attribute(a, value),
                                 })
        context['attributes'] = attributes
        return context


class InfoboxCompareView(CompareView):
    template_name = 'infobox/infobox_diff.html'

    def get_object(self):
        page_slug = self.kwargs.get('slug')
        page = Page.objects.get(slug=page_slug)
        return Entity(page)

    def get_object_as_of(self, version=None, date=None):
        return EntityAsOf(self.object.model, version=version, date=date)

    def get_context_data(self, **kwargs):
        context = super(InfoboxCompareView, self).get_context_data(**kwargs)
        context['slug'] = self.kwargs['original_slug']
        return context