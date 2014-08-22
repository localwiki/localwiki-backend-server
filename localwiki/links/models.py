from django.db import models
from django.utils.translation import ugettext_lazy as _

from pages.models import Page
from regions.models import Region


class Link(models.Model):
    """
    Model representing an internal href link between two
    LocalWiki pages.
    """
    source = models.ForeignKey(Page, related_name='links')
    destination = models.ForeignKey(Page, related_name='links_to_here', null=True)
    # We can link to pages that don't yet exist, so we record the page name as well.
    destination_name = models.CharField(max_length=255, editable=False, blank=False)
    count = models.PositiveSmallIntegerField(
        help_text=_("The number of times the source page links to the destination page."))

    region = models.ForeignKey(Region)

    class Meta:
        unique_together = ('source', 'destination')

    def __unicode__(self):
        return "%s ---> %s" % (self.source, self.destination_name)


class IncludedPage(models.Model):
    """
    Model representing an included page object.

    If page A includes page B, an IncludedPage model instance will be created
    with the values:

       m.source = A
       m.included_page = B
    """
    source = models.ForeignKey(Page, related_name='included_pages')
    included_page = models.ForeignKey(Page, related_name='pages_that_include_this', null=True)
    # We can include pages that don't yet exist, so we record the page name as well.
    included_page_name = models.CharField(max_length=255, editable=False, blank=False)

    region = models.ForeignKey(Region)

    class Meta:
        unique_together = ('source', 'included_page')

    def __unicode__(self):
        return "%s ---> %s" % (self.source, self.included_page_name)


# For registration calls
import signals
