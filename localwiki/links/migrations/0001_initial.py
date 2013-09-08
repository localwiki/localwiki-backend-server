# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Link'
        db.create_table('links_link', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(related_name='links_to_here', to=orm['pages.Page'])),
            ('destination', self.gf('django.db.models.fields.related.ForeignKey')(related_name='links', null=True, to=orm['pages.Page'])),
            ('destination_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('count', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('region', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['regions.Region'])),
        ))
        db.send_create_signal('links', ['Link'])

        # Adding unique constraint on 'Link', fields ['source', 'destination']
        db.create_unique('links_link', ['source_id', 'destination_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'Link', fields ['source', 'destination']
        db.delete_unique('links_link', ['source_id', 'destination_id'])

        # Deleting model 'Link'
        db.delete_table('links_link')


    models = {
        'links.link': {
            'Meta': {'unique_together': "(('source', 'destination'),)", 'object_name': 'Link'},
            'count': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'destination': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'links'", 'null': 'True', 'to': "orm['pages.Page']"}),
            'destination_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'region': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['regions.Region']"}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'links_to_here'", 'to': "orm['pages.Page']"})
        },
        'pages.page': {
            'Meta': {'unique_together': "(('slug', 'region'),)", 'object_name': 'Page'},
            'content': ('pages.fields.WikiHTMLField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'region': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['regions.Region']", 'null': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '255'})
        },
        'regions.region': {
            'Meta': {'object_name': 'Region'},
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'geom': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '255'})
        }
    }

    complete_apps = ['links']