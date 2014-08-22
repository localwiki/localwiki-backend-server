from django.db.models.signals import post_save, pre_delete

from pages.models import Page, slugify

from links import extract_internal_links, extract_included_pagenames
from models import Link, IncludedPage


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

############################
# Now for included pages:
############################

def record_page_includes(page):
    region = page.region
    included = extract_included_pagenames(page.content)
    for pagename in included:
        included_pg_exists = IncludedPage.objects.filter(
            source=page, region=region,
            included_page_name__iexact=pagename)
        if not included_pg_exists:
            page_exists = Page.objects.filter(slug=slugify(pagename), region=region)
            if page_exists:
                included_page = page_exists[0]
            else:
                included_page = None
            m = IncludedPage(
                source=page,
                region=region,
                included_page=included_page,
                included_page_name=pagename,
            )
            m.save()

def _record_page_includes(sender, instance, created, raw, **kws):
    # Don't create IncludedPages when importing via loaddata - they're already
    # being imported.
    if raw:
        return
    record_page_includes(instance)

def _check_included_page_created(sender, instance, created, raw, **kws):
    # Don't create IncludedPages when importing via loaddata - they're already
    # being imported.
    if raw:
        return
    if not created:
        return

    # The included page has been created, so let's record that.
    pages_that_include_this = IncludedPage.objects.filter(included_page_name__iexact=instance.slug)
    for m in pages_that_include_this:
        m.included_page = instance
        m.save()

def _remove_included_page_exists(sender, instance, **kws):
    # The page-being-included is being deleted, so let's record that.
    pages_that_include_this = IncludedPage.objects.filter(included_page_name__iexact=instance.slug)
    for m in pages_that_include_this:
        m.included_page = None
        m.save()


# TODO: make these happen in the background using a task queue.
# Links signals
post_save.connect(_record_page_links, sender=Page)
post_save.connect(_check_destination_created, sender=Page)
pre_delete.connect(_remove_destination_exists, sender=Page)

# Included page signals
post_save.connect(_record_page_includes, sender=Page)
post_save.connect(_check_included_page_created, sender=Page)
pre_delete.connect(_remove_included_page_exists, sender=Page)
