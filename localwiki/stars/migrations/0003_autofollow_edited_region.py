# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

from follow.models import Follow
from pages.models import Page

from django.contrib.auth.models import User


class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."
        # Note: Don't use "from appname.models import ModelName". 
        # Use orm.ModelName to refer to models in this application,
        # and orm['appname.ModelName'] for models in other applications.
        for u in User.objects.all():
            # If hasn't edited, skip.
            if not Page.versions.filter(history_user=u).exists():
                continue

            page_edits = Page.versions.filter(history_user=u)
            most_recent_region = page_edits[0].region

            if not Follow.objects.filter(user=u, target_region=most_recent_region):
                # Follow the most recently edited region
                print 'Following', most_recent_region, 'on user', u
                Follow(user=u, target_region=most_recent_region).save()
        

    def backwards(self, orm):
        "Write your backwards methods here."

    models = {
        
    }

    complete_apps = ['stars']
    symmetrical = True
