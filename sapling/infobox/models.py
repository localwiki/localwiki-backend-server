from django.db import models
from pages.models import Page
import eav
from eav.registry import EavConfig
from eav.models import BaseAttribute, BaseValue
from django.utils.translation import ugettext_lazy as _


class PageLink(models.Model):
    page_name = models.CharField(max_length=255, blank=True, null=True)


DAYS_OF_WEEK = (
    ('1', _(u'Sunday')),
    ('2', _(u'Monday')),
    ('3', _(u'Tuesday')),
    ('4', _(u'Wednesday')),
    ('5', _(u'Thursday')),
    ('6', _(u'Friday')),
    ('7', _(u'Saturday')), 
)


class WeeklySchedule(models.Model):
    """
    Has many WeeklyTimeBlock 
    """
    pass


class WeeklyTimeBlock(models.Model):
    week_day = models.CharField(max_length=1, choices=DAYS_OF_WEEK,
                                blank=False, null=False)
    start_time = models.TimeField(blank=False, null=False)
    end_time = models.TimeField(blank=False, null=False)

    schedule = models.ForeignKey(WeeklySchedule, blank=False, null=False,
                                 related_name='time_blocks')

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError('Starting time should be before ending time')


class PageAttribute(BaseAttribute):
    pass


class PageValue(BaseValue):
    attribute = models.ForeignKey(PageAttribute, db_index=True,
                                  verbose_name=_(u"attribute"))
    entity = models.ForeignKey(Page, blank=False, null=False)

    value_page = models.OneToOneField(PageLink, blank=True,
                                      null=True,
                                      verbose_name=_(u"page link"),
                                      related_name='eav_value')
    value_schedule = models.OneToOneField(WeeklySchedule,
                                          blank=True, null=True,
                                          verbose_name=_(u"weekly schedule"),
                                          related_name='eav_value')


eav.register(Page, PageAttribute, PageValue)