from datetime import datetime, timedelta
from itertools import groupby

from django.core.urlresolvers import reverse
from django.views.generic.list import ListView
from versionutils.versioning.views import UpdateView

from utils.views import CreateObjectMixin, PermissionRequiredMixin

from models import Event
from forms import EventForm


class EventListView(ListView):
    model = Event

    def get_queryset(self):
        # Only display events that occur in the future, plus ones that
        # have happened in the past 8 hours.
        return Event.objects.filter(
            time_start__gte=(datetime.now() - timedelta(hours=8))
        )

    def get_context_data(self, *args, **kwargs):
        def _the_day(e):
            return (e.time_start.year, e.time_start.month, e.time_start.day)

        context = super(EventListView, self).get_context_data(*args, **kwargs)
        by_day = []
        for d, events in groupby(self.get_queryset(), _the_day):
            # Add a user link attribute for use in the template.
            es = []
            for e in events:
                user_link = e.versions.as_of(version=1).version_info.user_link()
                e.user_link = user_link
                es.append(e)
            by_day.append((datetime(*d), es))
        context['events_by_day'] = by_day

        return context


class EventUpdateView(PermissionRequiredMixin, CreateObjectMixin, UpdateView):
    model = Event
    form_class = EventForm
    # TODO: Add event permission
    permission = 'pages.change_page'

    def get_object(self):
        return Event()

    def get_success_url(self):
        return reverse('events:list')

