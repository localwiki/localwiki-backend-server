from copy import copy

from .models import *


def fix_tags(region, pts_qs=None):
    """
    Ensure that the provided `PageTagSet`s point at
    `Tag` models /inside/ the provided `region`.
    """
    # XXX TODO: This should be no longer needed once we have a single
    # global `Tag` model rather than per-region `Tag` models.

    if not pts_qs:
        pts_qs = PageTagSet.objects.filter(region=region)
    # Exclude those that are already in the region
    #pts_qs = pts_qs.filter(tags__region=region)
    for pts in pts_qs:
        # For each version of the PageTagSet, make sure to change the associated
        # `Tag` point to the provided `region`.
        for pts_h in pts.versions.all():
            add = []
            remove = []
            for t_h in pts_h.tags.exclude(region=region):
                tag = Tag.objects.filter(slug=t_h.slug, region=region)
                if tag.exists():
                    tag = tag[0]
                else:
                    # Create new Tag
                    tag = Tag(
                        name=t_h.name,
                        slug=t_h.slug,
                        region=region
                    )
                    tag.save()
                new_t_h = tag.versions.most_recent()
                add.append(new_t_h)
                remove.append(t_h)
            pts_h.tags.remove(*remove)
            pts_h.tags.add(*add)
            pts_h.save()

        # Now do the same with the current, non-historical instance of the PageTagSet
        add = []
        remove = []
        for t in pts.tags.exclude(region=region):
            tag = Tag.objects.filter(slug=t.slug, region=region)
            if tag.exists():
                tag = tag[0]
            else:
                # Create new Tag
                tag = copy(t)
                tag.pk = None
                tag.region = region
                tag.save()

            add.append(tag)
            remove.append(t)
        pts.tags.remove(*remove)
        pts.tags.add(*add)
        pts.save(track_changes = False)
