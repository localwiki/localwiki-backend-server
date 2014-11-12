from versionutils.versioning.utils import is_versioned

from regions.models import Region
from pages.models import Page, PageFile
from redirects.models import Redirect
from tags.models import PageTagSet
from maps.models import MapData


def update_region_for_instance(m, region):
    if not hasattr(m, 'region'):
        # Doesn't have an explicit region attribute, so skip.
        return
    if is_versioned(m):
        for m_h in m.versions.all():
            m_h.region = region
            m_h.save()
        m.region = region
        m.save(track_changes=False)
    else:
        m.save()

def clear_regenerable_dependencies(page):
    from links.models import Link, IncludedPage, IncludedTagList
    from pages.cache import _page_cache_pre_delete

    links_from_here = Link.objects.filter(source=page)
    links_from_here.delete()

    links_to_here = Link.objects.filter(destination=page)
    links_to_here.delete()

    pages_included_here = IncludedPage.objects.filter(source=page)
    pages_included_here.delete()

    pages_that_include_this = IncludedPage.objects.filter(included_page=page)
    pages_that_include_this.delete()

    included_tags = IncludedTagList.objects.filter(source=page)
    included_tags.delete()

    # Clear the caches
    _page_cache_pre_delete(Page, page)

def move_to_region(region, pages=None, redirects=None):
    """
    Move the provided `pages` and `redirects` to `region`, updating
    all related objects accordingly.
    """
    from tags.models import PageTagSet
    from tags.tag_utils import fix_tags

    # XXX and TODO: right now this just rewrites the version history.  When we're
    # versioning Regions we should make this do something like
    # p.save(comment="Moved region"), etc.
    pages = pages or []
    redirects = redirects or []

    for p in pages:
        if Page(slug=p.slug, region=region).exists():
            # Page already exists in the new region, so let's
            # skip moving it.
            continue

        p._in_move = True
        clear_regenerable_dependencies(p)


        # Need to get these before moving the page itself.
        rel_objs = p._get_related_objs()
        slug_rel_objs = p._get_slug_related_objs()

        old_region = p.region
        update_region_for_instance(p, region)

        for _, rel_obj in rel_objs:
            if isinstance(rel_obj, list):
                for obj in rel_obj:
                    update_region_for_instance(obj, region)
            else:
                update_region_for_instance(rel_obj, region)

        for info in slug_rel_objs:
            unique_together = info["unique_together"]
            # We need to check to see if these objects exist already. Unlike
            # normal related objects, by-slug related objs can persist
            # when a page is deleted.
            def _get_lookup(unique_together, obj, region):
                d = {}
                for field in unique_together:
                    d[field] = getattr(obj, field)
                d['region'] = region
                return d

            for obj in info['objs']:
                obj_lookup = _get_lookup(unique_together, obj, region)
                if obj.__class__.objects.filter(**obj_lookup):
                    # Already exists, so let's skip it.
                    continue
                update_region_for_instance(obj, region)

            p._in_move = False

            fix_tags(region, pts_qs=PageTagSet.objects.filter(page=p))

            # Save page to fire signals
            p.save(track_changes=False)

    for r in redirects:
        update_region_for_instance(r.destination, region)
        update_region_for_instance(r, region)
