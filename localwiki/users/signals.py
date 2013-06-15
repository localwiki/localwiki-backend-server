from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from django.db.models.signals import post_save, pre_delete, post_syncdb

from models import UserProfile


def create_user_profile(sender, instance, created, raw, **kwargs):
    if raw:
        # Don't create UserProfiles when importing via loaddata - they're already
        # being imported.
        return
    if created:
        UserProfile.objects.create(user=instance)


post_save.connect(create_user_profile, sender=User)


def delete_user_profile(sender, instance, **kwargs):
    instance.userprofile.delete()

# Delete UserProfile when User is deleted.  We need to do this explicitly
# because we're monkeypatching the User model (for now).
pre_delete.connect(delete_user_profile, sender=User) 


def add_view_permissions(sender, **kwargs):
    """
    This syncdb hooks takes care of adding a view permission too all our 
    content types.
    """
    # for each of our content types
    for content_type in ContentType.objects.all():
        # build our permission slug
        codename = "view_%s" % content_type.model

        # if it doesn't exist..
        if not Permission.objects.filter(content_type=content_type, codename=codename):
            # add it
            Permission.objects.create(content_type=content_type,
                                      codename=codename,
                                      name="Can view %s" % content_type.name)
            print "Added view permission for %s" % content_type.name

# check for all our view permissions after a syncdb
post_syncdb.connect(add_view_permissions)
