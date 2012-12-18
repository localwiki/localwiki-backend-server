from versionutils import diff
from eav.models import Entity
from models import PageAttribute, PageValue
from infobox.templatetags.infobox_tags import render_attribute

class InfoboxDiff(diff.BaseModelDiff):
    def get_diff(self):
        diff_dict = {}
        attributes = PageAttribute.objects.all()
        for a in attributes:
            if a.slug in self.model1 or a.slug in self.model2: 
                first = self.model1.get(a.slug, None)
                second = self.model2.get(a.slug, None)
                diff_dict[a.name] = PageValueDiff(first, second, attribute=a)
        return diff_dict


class PageValueDiff(diff.BaseFieldDiff):
    attribute = None

    def __init__(self, field1, field2, attribute):
        super(PageValueDiff, self).__init__(field1, field2)
        self.attribute = attribute

    def get_diff(self):
        field_name = 'value_%s' % self.attribute.type
        left_value = getattr(self.field1, field_name, None)
        right_value = getattr(self.field2, field_name, None)
        return {'deleted': left_value, 'inserted': right_value}

    def as_html(self):
        diff_dict = self.get_diff()
        left = right = '<p></p>'
        left = render_attribute(self.attribute, diff_dict['deleted'])
        right = render_attribute(self.attribute, diff_dict['inserted'])
        return '<tr><td>%s</td><td>%s</td></tr>' % (left, right)


diff.register(Entity, InfoboxDiff)
diff.register(PageValue, PageValueDiff)
