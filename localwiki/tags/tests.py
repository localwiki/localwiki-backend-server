# coding=utf-8

from django.test import TestCase
from django.db import IntegrityError

from regions.models import Region
from tags.models import Tag, PageTagSet


class TagTest(TestCase):
    def setUp(self):
        self.region = Region(full_name='Test Region', slug='test_region')
        self.region.save()
        
    def test_bad_tags(self):
        t = Tag(name='', region=self.region)
        self.failUnlessRaises(IntegrityError, t.save, t)

        t = Tag(name='!', region=self.region)
        self.failUnlessRaises(IntegrityError, t.save, t)

        t = Tag(name='/', region=self.region)
        self.failUnlessRaises(IntegrityError, t.save, t)

        t = Tag(name=' ', region=self.region)
        self.failUnlessRaises(IntegrityError, t.save, t)

        t = Tag(name='-', region=self.region)
        self.failUnlessRaises(IntegrityError, t.save, t)

        t = Tag(name='!@#$%^&*()', region=self.region)
        self.failUnlessRaises(IntegrityError, t.save, t)

    def test_slug(self):
        t = Tag(name='Library of Congress', region=self.region)
        t.save()
        self.assertEqual(t.slug, 'libraryofcongress')

        t = Tag(name='Сочи 2014', region=self.region)
        t.save()
        self.assertEqual(t.slug, 'сочи2014'.decode('utf-8'))

    def test_fix_tags(self):
        """
        Test the `fix_tags` utility function.
        """
        from pages.models import Page
        from tags.tag_utils import fix_tags

        #########################
        # Create some test regions
        #########################
       
        sf = Region(full_name="San Francisco Test", slug='sftest')
        sf.save()

        mission = Region(full_name="Mission", slug="mission")
        mission.save()

        #########################
        # Create some test tags
        #########################

        park = Tag(name='park', region=sf)
        park.save()

        fun = Tag(name='fun', region=sf)
        fun.save()

        #########################
        # Add the tags to a test page
        #########################

        page = Page(name="Duboce Park", content="<p>Park.</p>", region=sf)
        page.save()

        pts = PageTagSet(
            page=page,
            region=sf
        )
        pts.save()
        pts.tags.add(park)
        pts.tags.add(fun)
        pts.save()

        # Now do something odd and make one of the referenced `Tag`s point
        # to a different region than the PageTagSet.
        fun.region = mission
        fun.save()

        self.assertTrue(pts.tags.filter(region=mission).exists())

        # Then attempt a fix:
        fix_tags(sf, PageTagSet.objects.filter(id=pts.id))

        pts = PageTagSet.objects.get(page=page, region=sf)
        self.assertFalse(pts.tags.filter(region=mission).exists())

        # Check that this is fixed in historical versions as well
        for pts_h in pts.versions.all():
            self.assertFalse(pts_h.tags.filter(region=mission).exists())
