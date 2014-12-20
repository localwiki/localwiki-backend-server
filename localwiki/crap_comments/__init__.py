from pages.plugins import register, insert_text_before
from pages.widgets import register_editor_plugin

import templatetags
import site

def comments(elem, context=None):
    title = elem.text
    before = '{%% comments "%s" %%} %s' % (title, elem.tail or '')
    insert_text_before(before, elem)
    elem.getparent().remove(elem)

register('comments', comments)
register_editor_plugin('commentbox')
