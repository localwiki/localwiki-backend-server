from django.db.models.signals import post_save, pre_delete

from pages.models import Page, slugify

from links import extract_internal_links
from models import Link


def record_page_links(page):
    region = page.region
    links = extract_internal_links(page.content)
    for pagename, count in links.iteritems():
        link_exists = Link.objects.filter(
            source=page, region=region,
            destination_name__iexact=pagename)
        if link_exists:
            link = link_exists[0]
            if link.count == count:
                # No new links with this name on this page, so skip updating.
                continue
            link.count = count
        else:
            page_exists = Page.objects.filter(slug=slugify(pagename), region=region)
            if page_exists:
                destination = page_exists[0]
            else:
                destination = None
            link = Link(
                source=page,
                region=region,
                destination=destination,
                destination_name=pagename,
                count=count,
            )
        link.save()

def _record_page_links(sender, instance, created, raw, **kws):
    # Don't create Links when importing via loaddata - they're already
    # being imported.
    if raw:
        return
    record_page_links(instance)

def _check_destination_created(sender, instance, created, raw, **kws):
    # Don't create Links when importing via loaddata - they're already
    # being imported.
    if raw:
        return
    if not created:
        return

    # The destination page has been created, so let's record that.
    links = Link.objects.filter(destination_name__iexact=instance.slug)
    for link in links:
        link.destination = instance
        link.save()

def _remove_destination_exists(sender, instance, **kws):
    # The destination page is being deleted, so let's record that.
    links = Link.objects.filter(destination_name__iexact=instance.slug)
    for link in links:
        link.destination = None
        link.save()


# TODO: make these happen in the background using a task queue.
post_save.connect(_record_page_links, sender=Page)
post_save.connect(_check_destination_created, sender=Page)
pre_delete.connect(_remove_destination_exists, sender=Page)
