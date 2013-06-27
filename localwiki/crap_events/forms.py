from django import forms

from widgets import EventWikiEditor, DateTimeWidget
from models import Event


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        widgets = {
            'time_start': DateTimeWidget(),
            'description': EventWikiEditor()
        }
