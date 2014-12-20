from django import forms
from django.utils.translation import ugettext as _ 

from versionutils.versioning.forms import CommentMixin

from widgets import EventWikiEditor, DateTimeWidget
from models import Event


class EventForm(CommentMixin, forms.ModelForm):
    class Meta:
        model = Event
        widgets = {
            'time_start': DateTimeWidget(),
            'description': EventWikiEditor()
        }
        exclude = ('comment',)  # we generate comment automatically

    def get_save_comment(self):
        return (_('Event "%s" added') % self.instance.title)
