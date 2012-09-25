from django import template
from django.template.loader import render_to_string
from infobox.forms import InfoboxForm, AddAttributeForm
from eav.models import WeeklySchedule


register = template.Library()


@register.simple_tag
def infobox(instance):
    config_cls = instance._eav_config_cls
    entity = getattr(instance, config_cls.eav_attr)
    attributes = []
    for a in entity.get_all_attributes():
        value = getattr(entity, a.slug, None)
        if value is None:
            continue
        attributes.append({ 'name': a.name,
                            'value': value
                          })
    return render_to_string('infobox/infobox_snippet.html',
                            { 'attributes': attributes })


@register.simple_tag(takes_context=True)
def infobox_form(context, entity):
    context.push()
    context['form'] = InfoboxForm(instance=entity)
    context['add_attribute_form'] = AddAttributeForm(instance=entity)
    rendered = render_to_string('infobox/infobox_form_snippet.html', context)
    return rendered


@register.filter
def render_attribute(value):
#    if issubclass(value, WeeklySchedule):
#        return 'schedule'
    return value