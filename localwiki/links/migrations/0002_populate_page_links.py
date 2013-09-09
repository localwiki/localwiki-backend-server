# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models
from django.utils.encoding import smart_str


class Migration(DataMigration):

    def forwards(self, orm):
        from pages.models import slugify
        from links import extract_internal_links

        for page in orm['pages.Page'].objects.all():
            region = page.region
            links = extract_internal_links(page.content)
            for pagename, count in links.iteritems():
                page_exists = orm['pages.Page'].objects.filter(slug=slugify(pagename), region=region)
                if page_exists:
                    destination = page_exists[0]
                else:
                    destination = None
                print "..recording page links on %s" % smart_str(pagename)
                link = orm.Link(
                    source=page,
                    region=region,
                    destination=destination,
                    destination_name=pagename,
                    count=count,
                )
                link.save()

    def backwards(self, orm):
        orm.Link.objects.all().delete()

    models = {
        'links.link': {
            'Meta': {'unique_together': "(('source', 'destination'),)", 'object_name': 'Link'},
            'count': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'destination': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'links_to_here'", 'null': 'True', 'to': "orm['pages.Page']"}),
            'destination_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'region': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['regions.Region']"}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'links'", 'to': "orm['pages.Page']"})
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
    symmetrical = True
