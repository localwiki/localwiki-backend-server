from pages.plugins import register, insert_text_before

import templatetags
import site

def comments(elem, context=None):
    value = elem.attrib.get('value', '')
    before = '{%% comments "%s" %%} %s' % (value,
                                            elem.tail or '')
    insert_text_before(before, elem)
    elem.getparent().remove(elem)

register('comments', comments)
