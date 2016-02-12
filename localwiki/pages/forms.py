import mimetypes
import re

from django import forms
from django.utils.translation import  ugettext_lazy as _

from versionutils.merging.forms import MergeMixin
from versionutils.versioning.forms import CommentMixin
from pages.models import Page, PageFile, slugify
from pages.widgets import WikiEditor
from versionutils.diff.daisydiff.daisydiff import daisydiff_merge


def _has_blacklist_title(content):
    if re.search(r'quickbooks.*phone.*', content):
        return True
    if re.search(r'quickbooks.*toll.*free', content):
        return True
    if re.search(r'844(.{0,3})?414(.{0,3})?4868', content):
        return True
    if re.search(r'855(.{0,3})?855(.{0,3})?3(0|o|O)9(0|o|O)', content):
        return True
    if re.search(r'866(.{0,3})?769(.{0,3})?8127', content):
        return True
    if re.search(r'844(.{0,3})?461(.{0,3})?2828', content):
        return True
    if re.search(r'8(0|o|O)(0|o|O)(.{0,3})?298(.{0,3})?2(0|o|O)42', content):
        return True
    if re.search(r'866(.{0,3})?570(.{0,3})?8594', content):
        return True
    if re.search(r'877(.{0,3})?523(.{0,3})?3678', content):
        return True
    if re.search(r'866(.{0,3})?644(.{0,3})?6697', content):
        return True
    if re.search(r'877(.{0,3})?875(.{0,3})?4888', content):
        return True

def _has_blacklist_content(content):
    if re.search(r'844(.{0,3})?414(.{0,3})?4868', content):
        return True
    if re.search(r'855(.{0,3})?855(.{0,3})?3(0|o|O)9(0|o|O)', content):
        return True
    if re.search(r'866(.{0,3})?769(.{0,3})?8127', content):
        return True
    if re.search(r'844(.{0,3})?461(.{0,3})?2828', content):
        return True
    if re.search(r'8(0|o|O)(0|o|O)(.{0,3})?298(.{0,3})?2(0|o|O)42', content):
        return True
    if re.search(r'866(.{0,3})?570(.{0,3})?8594', content):
        return True
    if re.search(r'877(.{0,3})?523(.{0,3})?3678', content):
        return True
    if re.search(r'866(.{0,3})?644(.{0,3})?6697', content):
        return True
    if re.search(r'877(.{0,3})?875(.{0,3})?4888', content):
        return True


class PageForm(MergeMixin, CommentMixin, forms.ModelForm):
    conflict_error = _(
        "Warning: someone else saved this page before you.  "
        "Please resolve edit conflicts and save again."
    )

    class Meta:
        model = Page
        fields = ('content',)
        widgets = {'content': WikiEditor()}

    def merge(self, yours, theirs, ancestor):
        # ancestor may be None
        ancestor_content = ''
        if ancestor:
            ancestor_content = ancestor['content']
        (merged_content, conflict) = daisydiff_merge(
            yours['content'], theirs['content'], ancestor_content
        )
        if conflict:
            self.data = self.data.copy()
            self.data['content'] = merged_content
            raise forms.ValidationError(self.conflict_error)
        else:
            yours['content'] = merged_content
        return yours

    def clean(self):
        cleaned_data = super(PageForm, self).clean()
        content = self.cleaned_data['content']
        if _has_blacklist_content(content):
            raise forms.ValidationError()
        return cleaned_data

    def clean_name(self):
        name = self.cleaned_data['name']
        try:
            page = Page.objects.get(slug__exact=slugify(name))
            if self.instance != page:
                raise forms.ValidationError(
                    _('A page with this name already exists')
                )
        except Page.DoesNotExist:
            pass

        if _has_blacklist_title(name):
            raise forms.ValidationError()

        return name


class PageFileForm(CommentMixin, forms.ModelForm):

    def clean(self):
        self.cleaned_data = super(PageFileForm, self).clean()
        if self.instance.name:
            filename = self.cleaned_data['file'].name
            (mime_type, enc) = mimetypes.guess_type(filename)
            if mime_type != self.instance.mime_type:
                raise forms.ValidationError(
                    _('The new file should be of the same type'))
        return self.cleaned_data

    class Meta:
        model = PageFile
        fields = ('file',)
