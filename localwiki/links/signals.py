from django.db.models.signals import post_save, pre_delete, post_delete

from pages.models import Page, slugify
from tags.models import Tag
from page_scores.models import _calculate_page_score

from links import extract_internal_links, extract_included_pagenames, extract_included_tags
from .models import Link, IncludedPage, IncludedTagList


def record_page_links(page):
    region = page.region
    links_before = list(page.links.all())
    links = extract_internal_links(page.content)
    for pagename, count in links.iteritems():
        qs = Link.objects.filter(source=page, region=region)
        link_exists = qs.filter(destination_name__iexact=pagename) | qs.filter(destination__slug=slugify(pagename))
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

        if link in links_before:
            links_before.remove(link)
    
    # Links that were removed when the page was edited
    for l in links_before:
        l.delete()

def _record_page_links(sender, instance, created, raw, **kws):
    # Don't create Links when importing via loaddata - they're already
    # being imported.
    if raw or getattr(instance, '_in_rename', False):
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

    # Remove included pages they've removed from the page
    to_delete = IncludedPage.objects.filter(source=page, region=region).exclude(included_page_name__in=included)
    for m in to_delete:
        m.delete()

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

def _record_tag_includes(sender, instance, created, raw, **kwargs):
    # Don't create IncludedTagLists when importing via loaddata - they're already
    # being imported.
    if raw or getattr(instance, '_in_rename', False):
        return
    record_tag_includes(instance)

def _new_link_fix_page_score(sender, instance, created, raw, **kwargs):
    # Don't create when importing via loaddata or renaming
    if raw or getattr(instance, '_in_rename', False):
        return
    if created and instance.destination:
        # TODO: If this is slow later on, maybe just od this on some link count threshold
        # (e.g. new count > total average link count)
        _calculate_page_score.delay(instance.destination.id)

def _deleted_link_fix_page_score(sender, instance, **kwargs):
    # Don't create when importing via loaddata or renaming
    if getattr(instance, '_in_rename', False):
        return
    if instance.destination:
        # TODO: If this is slow later on, maybe just od this on some link count threshold
        # (e.g. new count > total average link count)
        _calculate_page_score.delay(instance.destination.id)

# TODO: make these happen in the background using a task queue.
# Links signals
post_save.connect(_record_page_links, sender=Page)
post_save.connect(_check_destination_created, sender=Page)

# Included page signals
post_save.connect(_record_page_includes, sender=Page)
post_save.connect(_check_included_page_created, sender=Page)

# Included tag list signals
post_save.connect(_record_tag_includes, sender=Page)

# When links change we want to re-calculate the page score
post_save.connect(_new_link_fix_page_score, sender=Link)
pre_delete.connect(_deleted_link_fix_page_score, sender=Link)
