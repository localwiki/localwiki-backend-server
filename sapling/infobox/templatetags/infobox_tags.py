from django import template
from django.template.loader import render_to_string
from infobox.forms import InfoboxForm, AddAttributeForm
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


register = template.Library()


@register.simple_tag
def infobox(instance):
    config_cls = instance._eav_config_cls
    entity = getattr(instance, config_cls.eav_attr)
    attributes = []
    for a in entity.get_all_attributes():
        try:
            value = entity[a.slug]
        except KeyError:
            continue
        attributes.append({ 'name': a.name,
                            'html': render_attribute(a, value),
                          })
    return render_to_string('infobox/infobox_snippet.html',
                            { 'attributes': attributes })


@register.simple_tag(takes_context=True)
def infobox_form(context, entity):
    context.push()
    context['form'] = InfoboxForm(instance=entity)
    context['add_attribute_form'] = AddAttributeForm(instance=entity)
    rendered = render_to_string('infobox/infobox_form_snippet.html', context)
    rendered = str(context['form'].media) + rendered
    return rendered


def render_attribute(attribute, value):
    if attribute.datatype == attribute.TYPE_ENUM:
        value_list = ['<li>%s</li>' % v for v in value.all()]
        return mark_safe('<ul>%s</ul>' % ''.join(value_list))
    return value or _('Please edit and fill in!')
