from django import forms
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.forms.util import flatatt
from django.template.loader import render_to_string

from utils.static_helpers import static_url


class TagEdit(forms.TextInput):
    def autocomplete_url(self):
        return ('/_api/tags/suggest/')

    def render(self, name, value, attrs=None):
        input = super(TagEdit, self).render(name, value, attrs)
        return input + render_to_string('tags/tagedit.html',
                                        {'id': attrs['id'],
                                         'autocomplete_url': self.autocomplete_url()
                                         })
