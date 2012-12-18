from django import template
from django.template.loader import render_to_string
from infobox.forms import InfoboxForm, AddAttributeForm
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.utils.html import escape
from django.utils.dates import WEEKDAYS


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
        {'attributes': attributes})


@register.simple_tag(takes_context=True)
def infobox_form(context, entity, extra=None):
    context.push()
    context['form'] = InfoboxForm(instance=entity)
    if extra == "allowdelete":
        context['allowdelete'] = True
    rendered = render_to_string('infobox/infobox_form_snippet.html', context)
    rendered = str(context['form'].media) + rendered
    context.pop()
    return rendered


@register.simple_tag(takes_context=True)
def add_attribute_form(context, entity):
    form = AddAttributeForm(instance=entity)
    if len(form['attribute'].field.choices) == 0:
        rendered = ""
    else:
        context.push()
        context['form'] = form
        rendered = render_to_string('infobox/infobox_add_attribute_form.html',
                                    context)
        context.pop()
    return rendered


def render_schedule(schedule):
    """
    Render the schedule as HTML, grouping time blocks by day of the week.
    """
    if schedule is None:
        return '<p></p>'
    # TODO: doesn't work with historical instances!!
    params = {'time_blocks': schedule.time_blocks.all()}
    return render_to_string('infobox/weekly_schedule.html', params)


def render_attribute(attribute, value):
    """
    Render the attribute value nicely, taking into account its type. Returns a
    safe HTML string.
    """
    rendered = '<p></p>'  # default if no value
    if value is None:
        return mark_safe(rendered)
    if attribute.type == attribute.TYPE_ENUM:
        value_list = ['<li>%s</li>' % escape(v.value) for v in value.all()]
        if value_list:
            rendered = '<ul>%s</ul>' % ''.join(value_list)
    elif attribute.type == attribute.TYPE_SCHEDULE:
        rendered = render_schedule(value)
    elif attribute.type == attribute.TYPE_BOOLEAN:
        rendered = {True: _('Yes'), False: _('No'), None: rendered}.get(value)
    elif value:
        rendered = escape(value)
    return mark_safe(rendered)
