from django import forms

from widgets import EventWikiEditor

from models import Event


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        widgets = {'description': EventWikiEditor()}
