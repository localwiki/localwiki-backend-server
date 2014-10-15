from copy import copy

from django import template
from django.template.loader import render_to_string

from tags.models import slugify

register = template.Library()


@register.simple_tag(takes_context=True)
def filtered_tags(context, list, keywords, region_slug=None):
    list = list or []
    keywords = keywords or []
    unused = set(list)
    filtered = []
    for word in keywords:
        for tag in unused:
            if word.lower() in tag.lower():
                filtered.append(tag)
                unused.remove(tag)
                break
    if not filtered:
        return ''

    if region_slug:
        context['global'] = False
        tags = [{'name': t, 'slug': slugify(t), 'region': {'slug': region_slug}} for t in filtered]
    else:
        context['global'] = True
        tags = [{'name': t, 'slug': slugify(t)} for t in filtered]

    context = copy(context)
    context.update({'tag_list': tags})
    return render_to_string('tags/tag_list_snippet.html', context)
