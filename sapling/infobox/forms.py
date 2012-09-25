from copy import deepcopy
from django import forms
from eav.forms import BaseDynamicEntityForm
from django.forms.models import ModelForm, inlineformset_factory,\
    ModelChoiceField
from eav.models import Attribute, EnumGroup, EnumValue
from django.contrib.contenttypes.models import ContentType
from pages.models import Page
from django.contrib.admin.widgets import AdminSplitDateTime
from infobox.models import WeeklySchedule, WeeklyTimeBlock, PageLink


class InfoboxForm(BaseDynamicEntityForm):
    def save(self, commit=True):
        # we don't want to save the model instance, just the EAV attributes
        super(InfoboxForm, self).save(commit=False)
        self.entity.save()


class PageLinkForm(ModelForm):
    class Meta:
        model = PageLink


WeeklyTimeBlockFormSet = inlineformset_factory(WeeklySchedule, WeeklyTimeBlock,
                                               extra=7)


class WeeklyScheduleForm(WeeklyTimeBlockFormSet):
    def save(self, commit=True):
        self.instance.save()
        super(WeeklyScheduleForm, self).save(commit)
        return self.instance


class AddAttributeForm(ModelForm):
    attribute = ModelChoiceField(queryset=Attribute.objects.all())

    def __init__(self, *args, **kwargs):
        # we want to exclude attributes the entity already has
        super(AddAttributeForm, self).__init__(*args, **kwargs)
        config_cls = self.instance._eav_config_cls
        self.entity = getattr(self.instance, config_cls.eav_attr)
        already_has = [v.attribute.pk for v in self.entity.get_values()]
        self.fields['attribute'].queryset = Attribute.objects.exclude(
                                                            pk__in=already_has)

    def save(self, commit=False):
        attribute = self.cleaned_data.get('attribute', None)
        attribute.save_value(self.entity.model, None)


class AttributeCreateForm(ModelForm):
    class Meta:
        model = Attribute
        fields = ('name', 'description', 'datatype', 'enum_group')
        exclude = ('site','slug',)

    def save(self, *args, **kwargs):
        # tie attributes to Page model on save
        self.instance.parent = ContentType.objects.get_for_model(Page)
        return super(AttributeCreateForm, self).save(*args, **kwargs)


class AttributeUpdateForm(ModelForm):
    class Meta:
        model = Attribute
        fields = ('name', 'description')
