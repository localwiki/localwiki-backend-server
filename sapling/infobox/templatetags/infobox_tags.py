from django import template
from django.template.loader import render_to_string
from infobox.forms import InfoboxForm, AddAttributeForm


register = template.Library()


@register.simple_tag
def infobox(instance):
    attributes = [
        {'name': v.attribute.name, 'value': v.value}
        for v in instance.eav.get_values() if v.value is not None
    ]
    return render_to_string('infobox/infobox_snippet.html',
        {'attributes': attributes})


@register.simple_tag(takes_context=True)
def infobox_form(context, entity):
    context.push()
    context['form'] = InfoboxForm(instance=entity)
    context['add_attribute_form'] = AddAttributeForm(instance=entity)
    rendered = render_to_string('infobox/infobox_form_snippet.html', context)
    return rendered

