from django import forms
from eav.forms import BaseDynamicEntityForm
from django.forms.models import ModelForm, inlineformset_factory
from eav.models import Attribute, EnumGroup, EnumValue
from django.contrib.contenttypes.models import ContentType
from pages.models import Page


class InfoboxForm(BaseDynamicEntityForm):
    def __init__(self, data=None, *args, **kwargs):
        super(BaseDynamicEntityForm, self).__init__(data, *args, **kwargs)
        config_cls = self.instance._eav_config_cls
        self.entity = getattr(self.instance, config_cls.eav_attr)
        self._build_dynamic_fields()

    def save(self, commit=True):
        # we don't want to save the model instance, just the EAV attributes
        super(InfoboxForm, self).save(commit=False)
        self.entity.save()


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
