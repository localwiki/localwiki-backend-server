import html5lib
import urlparse

from pages.models import slugify, url_to_name

def _is_absolute(href):
    return bool(urlparse.urlparse(href).scheme)

def _is_anchor_link(href):
    return href.startswith('#')

def _invalid(href):
    return len(href) > 255
    
def extract_internal_links(html):
    """
    Args:
        html: A string containing an HTML5 fragment.

    Returns:
        A dictionary of the linked-to page names and the number of times that
        link has been made in this HTML.  E.g.
        {'Downtown Park': 3, 'Rollercoaster': 1}
    """
    parser = html5lib.HTMLParser(
        tree=html5lib.treebuilders.getTreeBuilder("lxml"),
        namespaceHTMLElements=False)
    # Wrap to make the tree lookup easier
    tree = parser.parseFragment('<div>%s</div>' % html)[0]
    hrefs = tree.xpath('//a/@href')

    # Grab the links if they're not anchors or external.
    d = {}
    for href in hrefs:
        if not _is_absolute(href) and not _is_anchor_link(href) and not _invalid(href):
            if not slugify(href) in d:
                d[slugify(href)] = (url_to_name(href), 1)
            else:
                name, count = d[slugify(href)]
                d[slugify(href)] = (name, count + 1)

    # Format the result correctly.
    links = {}
    for _, (name, count) in d.iteritems():
        links[name] = count
    
    return links


import site
