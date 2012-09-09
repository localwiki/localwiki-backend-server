from copy import deepcopy
from django import forms
from eav.forms import BaseDynamicEntityForm
from django.forms.models import ModelForm, inlineformset_factory,\
    ModelChoiceField
from eav.models import Attribute, EnumGroup, EnumValue
from django.contrib.contenttypes.models import ContentType
from pages.models import Page
from django.contrib.admin.widgets import AdminSplitDateTime


class InfoboxForm(BaseDynamicEntityForm):
    def __init__(self, data=None, *args, **kwargs):
        super(BaseDynamicEntityForm, self).__init__(data, *args, **kwargs)
        config_cls = self.instance._eav_config_cls
        self.entity = getattr(self.instance, config_cls.eav_attr)
        self._build_dynamic_fields()

    def _build_dynamic_fields(self):
        # reset form fields
        self.fields = deepcopy(self.base_fields)

        for v in self.entity.get_values():
            value = v.value
            attribute = v.attribute

            defaults = {
                'label': attribute.name.capitalize(),
                'required': attribute.required,
                'help_text': attribute.help_text,
                'validators': attribute.get_validators(),
            }

            datatype = attribute.datatype
            if datatype == attribute.TYPE_ENUM:
                # for enum enough standard validator
                defaults['validators'] = []

                enums = attribute.get_choices() \
                                 .values_list('id', 'value')

                choices = [('', '-----')] + list(enums)

                defaults.update({'choices': choices})
                if value:
                    defaults.update({'initial': value.pk})

            elif datatype == attribute.TYPE_DATE:
                defaults.update({'widget': AdminSplitDateTime})
            elif datatype == attribute.TYPE_OBJECT:
                continue

            MappedField = self.FIELD_CLASSES[datatype]
            self.fields[attribute.slug] = MappedField(**defaults)

            # fill initial data (if attribute was already defined)
            if value and not datatype == attribute.TYPE_ENUM: #enum done above
                self.initial[attribute.slug] = value

    def save(self, commit=True):
        # we don't want to save the model instance, just the EAV attributes
        super(InfoboxForm, self).save(commit=False)
        self.entity.save()


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
        exclude = ('site', 'slug')

    def save(self, *args, **kwargs):
        # tie attributes to Page model on save
        self.instance.parent = ContentType.objects.get_for_model(Page)
        return super(AttributeCreateForm, self).save(*args, **kwargs)


class AttributeUpdateForm(ModelForm):
    class Meta:
        model = Attribute
        fields = ('name', 'description')
