from django.contrib.gis.db import models


def get_all_related_objects_full(page):
    """
    Get all the related objects on `page`.  Freezes related sets
    as well.
    """
    related_objs = []
    for r in page._meta.get_all_related_objects():
        try:
            rel_obj = getattr(page, r.get_accessor_name())
        except:
            continue  # No object for this relation.

        # Is this a related /set/, e.g. redirect_set?
        if isinstance(rel_obj, models.Manager):
            # list() freezes the QuerySet, which we don't want to be
            # fetched /after/ we delete the page.
            related_objs.append(
                (r.get_accessor_name(), list(rel_obj.all())))
        else:
            related_objs.append((r.get_accessor_name(), rel_obj))

    # Cache all ManyToMany values on related objects so we can restore them
    # later--otherwise they will be lost when page is deleted.
    for attname, rel_obj_list in related_objs:
        if not isinstance(rel_obj_list, list):
            rel_obj_list = [rel_obj_list]
        for rel_obj in rel_obj_list:
            rel_obj._m2m_values = dict(
                (f.attname, list(getattr(rel_obj, f.attname).all()))
                for f in rel_obj._meta.many_to_many)

    return related_objs


def copy_related_objects(related_objs, slug_related_objs, page, comment=""):
    """
    Copy related objs and related-via-slug objects to `page`.
    """
    from redirects.exceptions import RedirectToSelf

    def _get_slug_lookup(unique_together, obj, new_p):
            d = {}
            for field in unique_together:
                d[field] = getattr(obj, field)
            d['slug'] = new_p.slug
            return d

    # Point each related object to the new page and save the object with a
    # 'was renamed' comment.
    for attname, rel_obj in related_objs:
        if isinstance(rel_obj, list):
            for obj in rel_obj:
                obj.pk = None  # Reset the primary key before saving.
                try:
                    getattr(page, attname).add(obj)
                    # XXX TODO: pass in comment=comment here when versioning is working on
                    # eav
                    obj.save()
                    # Restore any m2m fields now that we have a new pk
                    for name, value in obj._m2m_values.items():
                        setattr(obj, name, value)
                except RedirectToSelf, s:
                    # We don't want to create a redirect to ourself.
                    # This happens during a rename -> rename-back
                    # cycle.
                    continue
        else:
            # This is an easy way to set obj to point to new_p.
            setattr(page, attname, rel_obj)
            rel_obj.pk = None  # Reset the primary key before saving.
            # XXX TODO: pass in comment=comment here when versioning is working on
            # eav
            rel_obj.save()
            # Restore any m2m fields now that we have a new pk
            for name, value in rel_obj._m2m_values.items():
                setattr(rel_obj, name, value)

    # Do the same with related-via-slug objects.
    for info in slug_related_objs:
        unique_together = info['unique_together']
        objs = info['objs']
        for obj in objs:
            # If we already have the same object with this slug then
            # skip it. This happens when there's, say, a PageFile that's
            # got the same name that's attached to the page -- which can
            # happen during a page rename -> rename back cycle.
            obj_lookup = _get_slug_lookup(unique_together, obj, page)
            if obj.__class__.objects.filter(**obj_lookup):
                continue
            obj.slug = page.slug
            obj.pk = None  # Reset the primary key before saving.
            # XXX TODO: pass in comment=comment here when versioning is working on
            # eav   
            obj.save()
