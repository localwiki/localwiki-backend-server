from django.contrib import admin
from guardian.admin import GuardedModelAdmin
from eav.forms import BaseDynamicEntityForm
from eav.admin import BaseEntityAdmin, register_admin, AttributeAdmin

from pages.models import Page

from models import PageAttribute


class PageAdminForm(BaseDynamicEntityForm):
    model = Page


class PageAdmin(BaseEntityAdmin, GuardedModelAdmin):
    form = PageAdminForm


admin.site.unregister(Page)
admin.site.register(Page, PageAdmin)
register_admin()
admin.site.register(PageAttribute, AttributeAdmin)