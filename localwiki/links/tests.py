from django.test import TestCase

from links import extract_internal_links, extract_included_pagenames


class ExtractLinkTest(TestCase):
    def test_simple_extraction(self):
        html = """
<p>I love <a href="Parks">awesome parks</a>.</p>
        """
        links = extract_internal_links(html)
        self.assertTrue('Parks' in links)
        self.assertEqual(links['Parks'], 1)

    def test_count_links(self):
        html = """
<p>I love <a href="Parks">awesome parks</a>.</p>
<p>I hate <a href="Cats%20and%20dogs">animals</a>.</p>
<p>I love <a href="Parks">awesome parks</a>.</p>
<p>I love <a href="Parks">awesome parks</a>.</p>
<p>I love <a href="Cats%20and%20dogs">awesome parks</a>.</p>
        """
        links = extract_internal_links(html)
        self.assertTrue('Parks' in links)
        self.assertTrue('Cats and dogs' in links)
        self.assertEqual(links['Parks'], 3)
        self.assertEqual(links['Cats and dogs'], 2)

    def test_link_unquoting(self):
        html = """
<p>I love <a href="Cats%20and%20dogs">animals</a>.</p>
<p>I love <a href="Cats and dogs">animals</a>.</p>
        """
        links = extract_internal_links(html)
        self.assertTrue('Cats and dogs' in links)
        self.assertFalse('Cats%20and%20dogs' in links)

    def test_ignore_external_links(self):
        html = """
<p>I love <a href="Parks">outside</a>.</p>
<p>I love <a href="http://example.org/Night">test</a>.</p>
        """
        links = extract_internal_links(html)
        self.assertTrue('Parks' in links)
        self.assertEqual(len(links.keys()), 1)

    def test_ignore_anchors(self):
        html = """
<p>I love <a href="Parks">outside</a>.</p>
<p>I love <a href="#gohere">test</a>.</p>
<p>I love <a>test now</a>.</p>
        """
        links = extract_internal_links(html)
        self.assertTrue('Parks' in links)
        self.assertEqual(len(links.keys()), 1)


class ExtractIncludedPagesTest(TestCase):
    def test_simple_extraction(self):
        html = """
<p>I love <a href="Parks" class="plugin includepage"></a>.</p>
        """
        included_pagenames = extract_included_pagenames(html)
        self.assertTrue('Parks' in included_pagenames)

    def test_link_unquoting(self):
        html = """
<p>I love <a href="Cats%20and%20dogs" class="includepage plugin right"></a>.</p>
<p>I love <a href="Cats and dogs" class="plugin includepage left"></a>.</p>
        """
        included_pagenames = extract_included_pagenames(html)
        self.assertTrue('Cats and dogs' in included_pagenames)
        self.assertFalse('Cats%20and%20dogs' in included_pagenames)

    def test_ignore_other_links(self):
        html = """
<p>I love <a href="Parks">outside</a>.</p>
<p>I love <a href="http://example.org/Night">test</a>.</p>
        """
        included_pagenames = extract_included_pagenames(html)
        self.assertFalse('Parks' in included_pagenames)
        self.assertTrue(included_pagenames == [])

    def test_ignore_anchors(self):
        html = """
<p>I love <a href="Parks" class="plugin includepage">outside</a>.</p>
<p>I love <a href="#gohere">test</a>.</p>
<p>I love <a>test now</a>.</p>
        """
        included_pagenames= extract_included_pagenames(html)
        self.assertTrue('Parks' in included_pagenames)
        self.assertEqual(len(included_pagenames), 1)
