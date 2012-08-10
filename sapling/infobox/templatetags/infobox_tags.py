from django import template
from django.template.loader import render_to_string
from infobox.forms import InfoboxForm


register = template.Library()


@register.simple_tag
def infobox(entity):
    return render_to_string('infobox/infobox_snippet.html')


@register.simple_tag(takes_context=True)
def infobox_form(context, entity):
    context.push()
    context['form'] = InfoboxForm(instance=entity)
    rendered = render_to_string('infobox/infobox_form_snippet.html', context)
    return rendered


@register.simple_tag
def infobox_form_media():
    f = InfoboxForm()
    return f.media
