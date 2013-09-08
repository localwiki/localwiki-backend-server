from django.db.models.signals import post_save
from pages.models import Page


def extract_links(sender, instance, raw, **kws):
    # Don't create Links when importing via loaddata - they're already
    # being imported.
    if raw:
        return
    import pdb;pdb.set_trace()

post_save.connect(extract_links, sender=Page)
