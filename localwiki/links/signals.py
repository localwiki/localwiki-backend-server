from django.db.models.signals import post_save
from pages.models import Page

from links import extract_internal_links


def _create_page_links(sender, instance, raw, **kws):
    # Don't create Links when importing via loaddata - they're already
    # being imported.
    if raw:
        return


post_save.connect(_create_page_links, sender=Page)
