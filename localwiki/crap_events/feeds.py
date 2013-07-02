from django.utils.translation import ugettext as _

import recentchanges
from recentchanges import RecentChanges
from recentchanges.feeds import ChangesOnItemFeed, MAX_CHANGES
from recentchanges.feeds import skip_ignored_change_types
from pages.models import Page

from models import Event


class EventChanges(RecentChanges):
    classname = 'event'

    def queryset(self, start_at=None):
        if start_at:
            return Event.versions.filter(version_info__date__gte=start_at)
        return Event.versions.all()

    def title(self, obj):
        return _('Event "%s"') % obj.title

    def page(self, obj):
        return Page(name='Events Board')

    def diff_url(self, obj):
        return ''

    def as_of_url(self, obj):
        return ''

recentchanges.register(EventChanges)
