from django.core.urlresolvers import reverse
from django.views.generic.list import ListView
from django.views.generic.edit import UpdateView

from utils.views import CreateObjectMixin, PermissionRequiredMixin

from models import Event


class EventListView(ListView):
    model = Event


class EventUpdateView(CreateObjectMixin, UpdateView):
    model = Event

    def get_object(self):
        return Event()

    def get_success_url(self):
        return reverse('events:list')

