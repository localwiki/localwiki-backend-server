# -*- coding: utf-8 -*-

from django.utils.translation import ugettext as _
from django.views.generic.edit import FormView
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect

from pages.models import Page

from forms import CommentForm

class AddCommentView(FormView):
    form_class = CommentForm

    def form_valid(self, form):
        comment = form.cleaned_data.get('content')
        page = Page.objects.get(slug=self.kwargs.get('slug'))

        if self.request.user.is_authenticated():
            # Because we're embedding this URL in the page's semi-special
            # HTML content, we don't want it to have a leading slash --
            # all wiki-links are relative, at least right now.
            user_url = self.request.user.get_absolute_url()[1:]
            user_info = '<a href="%s">%s</a>' % (user_url, self.request.user)
        else:
            if getattr(settings, 'SHOW_IP_ADDRESSES', True):
                user_info = self.request.META.get('REMOTE_ADDR', None)
            else:
                user_info = 'unknown'

        new_page_content = u"""%(current_html)s
<hr><p>
<em>%(datetime)s</em>   %(comment)s —%(user_info)s
</p>""" % {
            'current_html': page.content,
            'datetime': '',
            'comment': comment,
            'user_info': user_info,
        }

        page.content = new_page_content
        page.save()
        messages.add_message(self.request, messages.SUCCESS, self.success_msg())

        return super(AddCommentView, self).form_valid(form)

    def success_msg(self):
        # NOTE: This is eventually marked as safe when rendered in our
        # template.  So do *not* allow unescaped user input!
        return ('<div>' + _('Your comment was added. ') + '</div>')

    def get_success_url(self):
        return reverse('pages:show', args=[self.kwargs['slug']])
