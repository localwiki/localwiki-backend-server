from django.contrib import admin

from guardian.admin import GuardedModelAdmin
from eav.forms import BaseDynamicEntityForm
from eav.admin import BaseEntityAdmin, AttributeAdmin, EnumGroupAdmin

from pages.models import Page
from models import PageAttribute
from eav.models import EnumGroup


class PageAdminForm(BaseDynamicEntityForm):
    model = Page


class PageAdmin(BaseEntityAdmin, GuardedModelAdmin):
    form = PageAdminForm


class MultipleChoiceGroup(EnumGroup):
    """
    Proxy model for the purpose of grouping with our infobox app in the admin.
    """
    class Meta:
        proxy = True
        app_label = 'infobox'


admin.site.unregister(Page)
admin.site.register(Page, PageAdmin)
admin.site.register(MultipleChoiceGroup, EnumGroupAdmin)
admin.site.register(PageAttribute, AttributeAdmin)
