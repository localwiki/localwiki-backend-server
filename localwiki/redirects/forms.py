from django import forms
from django.utils.translation import ugettext_lazy as _

from versionutils.versioning.forms import CommentMixin
from pages.models import Page
from pages.fields import PageChoiceField
from utils.static_helpers import static_url

from models import Redirect


class RedirectForm(CommentMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        region = kwargs.pop('region', None)
        super(RedirectForm, self).__init__(*args, **kwargs)

        self.fields['destination'] = PageChoiceField(region=region, label=_("Destination"))

    class Meta:
        model = Redirect
        exclude = ('source', 'region')
