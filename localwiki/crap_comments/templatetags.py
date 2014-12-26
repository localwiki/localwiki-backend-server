from xml.sax.saxutils import escape

from django.utils.translation import ugettext as _
from django.template.loader import get_template
from django.template import RequestContext
from django.utils.text import unescape_string_literal

# Register this template tag as a pages template tag
from pages.templatetags.pages_tags import register
from pages.utils import is_user_page

from forms import CommentForm

@register.simple_tag(takes_context=True)
def comments(context, title):
    request = context['request']
    page = context['page']

    # Only enable on Davis region or user pages for now.
    if not (page.region.slug == 'davis' or is_user_page(page)):
        return ''

    if request.method == 'POST':
        form = CommentForm(request.POST)
    else:
        form = CommentForm()

    t = get_template('crap_comments/comment_form.html')
    return t.render(RequestContext(request, {
        'title': title or _('Comments:'),
        'page': page,
        'can_comment': request.user.is_authenticated() and request.user.has_perm('pages.change_page', page),
        'form': CommentForm(),
    }))
