from django import forms

from pages.widgets import WikiEditor

from models import Event


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        widgets = {'description': WikiEditor()}
