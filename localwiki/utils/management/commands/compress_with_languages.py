"""
A replacement for the django-compressor `compress` management command that renders all
templates with each `LANGUAGE_CODE` available in your `settings.LANGUAGES`.

Useful for making static-i18n work with django-compressor, among other things.
"""

import os
from os.path import join
import json
from copy import copy

from django.core.management.base import BaseCommand
from django.core.management import call_command

from compressor.conf import settings

ORIGINAL_COMPRESS_OFFLINE_CONTEXT = settings.COMPRESS_OFFLINE_CONTEXT
ORIGINAL_OFFLINE_MANIFEST = settings.COMPRESS_OFFLINE_MANIFEST 


class Command(BaseCommand):
    help = ('Just like `compress`, but iterates through LANGUAGES.')

    def handle(self, *args, **options):
        manifest = {}

        MANIFEST_ROOT = join(settings.STATIC_ROOT, 'CACHE')
        
        # Write a bunch of different manifests for each language
        for code, description in settings.LANGUAGES:
            COMPRESS_OFFLINE_CONTEXT = copy(ORIGINAL_COMPRESS_OFFLINE_CONTEXT)
            COMPRESS_OFFLINE_CONTEXT['LANGUAGE_CODE'] = code
            settings.COMPRESS_OFFLINE_CONTEXT = COMPRESS_OFFLINE_CONTEXT
            settings.COMPRESS_OFFLINE_MANIFEST = '%s_manifest.json' % code
            call_command('compress', *args, **options)
            manifest_for_code = json.load(open(join(MANIFEST_ROOT, '%s_manifest.json' % code)))
            manifest.update(manifest_for_code)
            os.remove(join(MANIFEST_ROOT, '%s_manifest.json' % code))
       
        # Combine them all into one manifest
        f = open(join(MANIFEST_ROOT, ORIGINAL_OFFLINE_MANIFEST), 'w')
        json.dump(manifest, f)
        f.close()
