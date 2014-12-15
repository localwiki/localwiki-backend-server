# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from django.utils.encoding import smart_text


class Migration(SchemaMigration):

    def forwards(self, orm):
        from pages.models import slugify

        # Adding field 'Link.destination_slug'
        db.add_column(u'links_link', 'destination_slug',
                      self.gf('django.db.models.fields.CharField')(default='testingo', max_length=255, db_index=True),
                      keep_default=False)

        # Adding field 'IncludedPage.included_page_slug'
        db.add_column(u'links_includedpage', 'included_page_slug',
                      self.gf('django.db.models.fields.CharField')(default='testingo', max_length=255, db_index=True),
                      keep_default=False)

        for link in orm['links.Link'].objects.all().defer('destination', 'source').iterator():
            link.destination_slug = slugify(link.destination_name)
            link.save()

        for included in orm['links.IncludedPage'].objects.all().defer('source', 'included_page').iterator():
            included.included_page_slug = slugify(included.included_page_name)
            included.save()

    def backwards(self, orm):
        # Deleting field 'Link.destination_slug'
        db.delete_column(u'links_link', 'destination_slug')

        # Deleting field 'IncludedPage.included_page_slug'
        db.delete_column(u'links_includedpage', 'included_page_slug')


    models = {
        u'links.includedpage': {
            'Meta': {'unique_together': "(('source', 'included_page'),)", 'object_name': 'IncludedPage'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'included_page': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pages_that_include_this'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['pages.Page']"}),
            'included_page_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'included_page_slug': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
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
            'destination_slug': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
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
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '255'})
        },
        u'tags.tag': {
            'Meta': {'ordering': "('slug',)", 'unique_together': "(('slug', 'region'),)", 'object_name': 'Tag'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'region': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['regions.Region']", 'null': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'})
        }
    }

    complete_apps = ['links']
