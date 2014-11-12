from django.db.models.signals import post_save, pre_delete, post_delete

from pages.models import Page, slugify
from tags.models import Tag

from links import extract_internal_links, extract_included_pagenames, extract_included_tags
from .models import Link, IncludedPage, IncludedTagList


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

            # Exists for some reason already (probably running a script that's moving between regions?)
            if destination and Link.objects.filter(source=page, destination=destination).exists():
                continue

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
    if raw or getattr(instance, '_in_rename', False) or getattr(instance, '_in_move', False):
        return
    record_page_links(instance)

def _check_destination_created(sender, instance, created, raw, **kws):
    # Don't create Links when importing via loaddata - they're already
    # being imported.
    if raw or getattr(instance, '_in_rename', False):
        return
    if not created:
        return

    # The destination page has been created, so let's record that.
    links = Link.objects.filter(destination_name__iexact=instance.slug, region=instance.region)
    for link in links:
        # May have already been added via a revert
        if Link.objects.filter(destination=instance, source=link.source, region=instance.region).exists():
            continue
        link.destination = instance
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
    if raw or getattr(instance, '_in_rename', False):
        return
    record_page_includes(instance)

def _check_included_page_created(sender, instance, created, raw, **kws):
    # Don't create IncludedPages when importing via loaddata - they're already
    # being imported.
    if raw or getattr(instance, '_in_rename', False):
        return
    if not created:
        return

    # The included page has been created, so let's record that.
    pages_that_include_this = IncludedPage.objects.filter(
        included_page_name__iexact=instance.slug, region=instance.region)
    for m in pages_that_include_this:
        m.included_page = instance
        m.save()


##########################################
# Now for included "list of tagged pages"
##########################################

def record_tag_includes(page):
    region = page.region
    included = extract_included_tags(page.content)
    
    for tag_slug in included:
        included_tag_exists = IncludedTagList.objects.filter(
            source=page,
            region=region,
            included_tag__slug=tag_slug)
        if not included_tag_exists:
            tag_exists = Tag.objects.filter(slug=tag_slug, region=region)
            if tag_exists:
                included_tag = tag_exists[0]
            else:
                continue
            m = IncludedTagList(
                source=page,
                region=region,
                included_tag=included_tag,
            )
            m.save()

    # Remove tag lists they've removed from the page
    to_delete = IncludedTagList.objects.filter(source=page, region=region).exclude(included_tag__slug__in=included)
    for m in to_delete:
        m.delete()

def _record_tag_includes(sender, instance, created, raw, **kws):
    # Don't create IncludedTagLists when importing via loaddata - they're already
    # being imported.
    if raw or getattr(instance, '_in_rename', False):
        return
    record_tag_includes(instance)

# TODO: make these happen in the background using a task queue.
# Links signals
post_save.connect(_record_page_links, sender=Page)
post_save.connect(_check_destination_created, sender=Page)

# Included page signals
post_save.connect(_record_page_includes, sender=Page)
post_save.connect(_check_included_page_created, sender=Page)

# Included tag list signals
post_save.connect(_record_tag_includes, sender=Page)
