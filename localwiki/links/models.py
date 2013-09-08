from django.db import models

from pages.models import Page
from regions.models import Region


class Link(models.Model):
    source = models.ForeignKey(Page, related_name='links_to_here')
    destination = models.ForeignKey(Page, related_name='links', null=True)
    destination_name = models.CharField(max_length=255, editable=False, blank=False)
    region = models.ForeignKey(Region)

    class Meta:
        unique_together = ('source', 'destination')

    def __unicode__(self):
        return "%s ---> %s" % (self.source, self.destination)


# For registration calls
import signals
