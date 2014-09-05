# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Link.destination'
        db.alter_column(u'links_link', 'destination_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, on_delete=models.SET_NULL, to=orm['pages.Page']))

        # Changing field 'IncludedPage.included_page'
        db.alter_column(u'links_includedpage', 'included_page_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, on_delete=models.SET_NULL, to=orm['pages.Page']))

    def backwards(self, orm):

        # Changing field 'Link.destination'
        db.alter_column(u'links_link', 'destination_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['pages.Page']))

        # Changing field 'IncludedPage.included_page'
        db.alter_column(u'links_includedpage', 'included_page_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['pages.Page']))

    models = {
        u'actstream.action': {
            'Meta': {'ordering': "('-timestamp',)", 'object_name': 'Action'},
            'action_object_content_type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'action_object'", 'null': 'True', 'to': u"orm['contenttypes.ContentType']"}),
            'action_object_object_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'actor_content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'actor'", 'to': u"orm['contenttypes.ContentType']"}),
            'actor_object_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'target_content_type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'target'", 'null': 'True', 'to': u"orm['contenttypes.ContentType']"}),
            'target_object_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'verb': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'links.includedpage': {
            'Meta': {'unique_together': "(('source', 'included_page'),)", 'object_name': 'IncludedPage'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'included_page': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pages_that_include_this'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['pages.Page']"}),
            'included_page_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'region': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['regions.Region']"}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'included_pages'", 'to': u"orm['pages.Page']"})
        },
        u'links.includedtaglist': {
            'Meta': {'unique_together': "(('source', 'included_tag'),)", 'object_name': 'IncludedTagList'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'included_tag': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pages_that_include_tag_list'", 'null': 'True', 'to': u"orm['tags.Tag']"}),
            'region': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['regions.Region']"}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'included_tag_lists'", 'to': u"orm['pages.Page']"})
        },
        u'links.link': {
            'Meta': {'unique_together': "(('source', 'destination'),)", 'object_name': 'Link'},
            'count': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'destination': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'links_to_here'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['pages.Page']"}),
            'destination_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'region': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['regions.Region']"}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'links'", 'to': u"orm['pages.Page']"})
        },
        u'pages.page': {
            'Meta': {'unique_together': "(('slug', 'region'),)", 'object_name': 'Page'},
            'content': ('pages.fields.WikiHTMLField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'region': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['regions.Region']", 'null': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        },
        u'regions.region': {
            'Meta': {'object_name': 'Region'},
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'geom': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '255'})
        },
        u'tags.tag': {
            'Meta': {'ordering': "('slug',)", 'unique_together': "(('slug', 'region'),)", 'object_name': 'Tag'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'region': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['regions.Region']", 'null': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['links']