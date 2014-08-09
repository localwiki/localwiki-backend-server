"""
We don't use a fixture here because:

    1. Each set of pages needs to point to a different region.  Not sure how
       to do this using fixtures.
    2. Translations are easier.
"""

from django.utils.translation import ugettext as _

from pages.models import Page, slugify

def populate_region(region):
    Page(
        name="Front Page",
        slug="front page",
        content=(_("""<p>
    	Welcome to the new LocalWiki region for %(region)s!
    <p>
    	Click on <strong>Explore</strong> at the top to see what's here now.</p>
    <p>
    	You can edit this and any other page by clicking the <strong>Edit</strong> button.</p>
    <p>Need <strong>help</strong>? Please see the <a href="http://localwiki.net/main/Help">help page</a> on the <a href="http://localwiki.net/main/">LocalWiki Guide</a>!</p>""") % {'region': region.full_name}),
        region=region
    ).save()
