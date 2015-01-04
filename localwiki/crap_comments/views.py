# -*- coding: utf-8 -*-
import time

from django.utils.translation import ugettext as _
from django.views.generic.edit import FormView
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect

from pages.models import Page
from regions.views import RegionMixin
from utils.views import AuthenticationRequired

from forms import CommentForm


class AddCommentView(RegionMixin, AuthenticationRequired, FormView):
    form_class = CommentForm

    def form_valid(self, form):
        comment = form.cleaned_data.get('content')
        self.page = Page.objects.get(slug=self.kwargs.get('slug'), region=self.get_region())

        user_url = 'Users/%s' % self.request.user.username
        user_info = '<a href="%s">%s</a>' % (user_url, self.request.user)

        new_page_content = u"""%(current_html)s
<hr><p>
<em>%(datetime)s</em> &nbsp; %(comment)s —%(user_info)s
</p>""" % {
            'current_html': self.page.content,
            'datetime': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            'comment': comment,
            'user_info': user_info,
        }

        self.page.content = new_page_content
        self.page.save(comment=_("Comment added"))
        messages.add_message(self.request, messages.SUCCESS, self.success_msg())

        return super(AddCommentView, self).form_valid(form)

    def success_msg(self):
        # NOTE: This is eventually marked as safe when rendered in our
        # template.  So do *not* allow unescaped user input!
        return ('<div>' + _('Your comment was added. ') + '</div>')

    def get_success_url(self):
        return self.page.get_absolute_url()
