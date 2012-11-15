"""
Ideal infobox API interaction:

/api/page_info/

GET /page_info/Alamo_Square_Park

    {
        'page': '/api/page/Alamo_Square_Park',
        'resource_uri': '/api/page_info/Alamo_Square_Park',
        'data': {
            'key1': 'value1',
            'key2': 'value2',
            'key3': 3.141592,
            '
            ...
        },
    }

gives lame implementation:

/page_info/?data__has_wifi=True
/page/?info__data__has_wifi=True

OR:

    {
        'page': '/api/page/Alamo_Square_Park',
        'resource_uri': '/api/page_info/Alamo_Square_Park',
        'key1': 'value1',
        'key2': 'value2',
        'key3': 3.141592,
        '
        ...
    }

/page_info/?has_wifi=True
/page/?info__has_wifi=True


OR [ much easier implementation ]:

/page_info/

GET /page_info/

{
   'id': 44,
   'attribute': 'has_wifi',
   'value': 'value1',
   'page': '/api/page/Alamo_Square_Park',
}

/page_info/?attribute=has_wifi&value=value1


GET /page_info_attribute/

{
    'id': 89,
    'attribute': 'has_wifi',
    'type': 'boolean',
    'name': 'Has wifi?',
    ...
}

"""

from tastypie.resources import (Resource, Bundle, ModelResource,
    ALL, ALL_WITH_RELATIONS)
from tastypie import fields
from tastypie.utils import dict_strip_unicode_keys
from tastypie.exceptions import InvalidFilterError
from tastypie.authentication import Authentication
from tastypie.authorization import Authorization

from django.db.models.sql.constants import QUERY_TERMS, LOOKUP_SEP

from sapling.api import api
from sapling.api.authentication import ApiKeyWriteAuthentication
from sapling.api.authorization import ChangePageAuthorization

from models import PageAttribute, PageValue


class InfoValue(object):
    def __init__(self, value=None):
        if value is None:
            return

        self.id = value.id
        self.value = value
        self.attribute = self.value.attribute.slug
        self.page = self.value.entity


AUTOMATIC_DATATYPES = [
    PageAttribute.TYPE_TEXT,
    PageAttribute.TYPE_FLOAT,
    PageAttribute.TYPE_INT,
    PageAttribute.TYPE_BOOLEAN,
    PageAttribute.TYPE_BOOLEAN,
]


def to_attr_datatype(o, attribute):
    """
    Args:
        o: a JSON-like object.
        attribute: an Attribute instance.

    Returns:
        o cast to the datatype of the provided attribute.
    """
    if attribute.datatype in AUTOMATIC_DATATYPES:
        return o

    if attribute.datatype is PageAttribute.TYPE_DATE:
        f = fields.DateTimeField()
        return f.convert(o)

    raise TypeError("The datatype %s is not supported via the API yet" %
        attribute.datatype)


class FilteringAndSortingMixin(object):
    def build_filters(self, filters=None):
        """
        This is essential ModelResource.build_filters, except we don't check
        for the existance of the queryset meta attribute (which is the thing
        that prevents us from using ModelResource.build_filters directly.
        """
        # Accepts the filters as a dict. None by default, meaning no filters.
        if filters is None:
            filters = {}

        qs_filters = {}

        query_terms = QUERY_TERMS.keys()

        for filter_expr, value in filters.items():
            filter_bits = filter_expr.split(LOOKUP_SEP)
            field_name = filter_bits.pop(0)
            filter_type = 'exact'

            if not field_name in self.fields:
                # It's not a field we know about. Move along citizen.
                continue

            if len(filter_bits) and filter_bits[-1] in query_terms:
                filter_type = filter_bits.pop()

            lookup_bits = self.check_filtering(field_name, filter_type, filter_bits)
            value = self.filter_value_to_python(value, field_name, filters, filter_expr, filter_type)

            db_field_name = LOOKUP_SEP.join(lookup_bits)
            qs_filter = "%s%s%s" % (db_field_name, LOOKUP_SEP, filter_type)
            qs_filters[qs_filter] = value

        return dict_strip_unicode_keys(qs_filters)

    def check_filtering(self, *args, **kwargs):
        return ModelResource.check_filtering.__func__(self, *args, **kwargs)

    def filter_value_to_python(self, *args, **kwargs):
        return ModelResource.filter_value_to_python.__func__(
            self, *args, **kwargs)


class InfoResource(FilteringAndSortingMixin, Resource):
    id = fields.IntegerField(attribute='id')
    attribute = fields.CharField(attribute='attribute')
    page = fields.ToOneField('pages.api.PageResource', 'page')

    class Meta:
        resource_name = 'page_info'
        object_class = InfoValue
        list_allowed_methods = ['get', 'post']
        filtering = {
            'attribute': ALL,
        }
        #authentication = ApiKeyWriteAuthentication()
        #authorization = ChangePageAuthorization()
        authentication = Authentication()
        authorization = Authorization()

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}

        if isinstance(bundle_or_obj, Bundle):
            obj = bundle_or_obj.obj
            attribute = PageAttribute.objects.get(slug=obj.attribute)
            value = PageValue.objects.get(entity=obj.page, attribute=attribute)
            kwargs['pk'] = value.id
        else:
            kwargs['pk'] = bundle_or_obj.value.id

        return kwargs

    def dehydrate(self, bundle):
        bundle.data['value'] = bundle.obj.value.value
        return bundle

    def full_hydrate(self, bundle):
        bundle = super(InfoResource, self).full_hydrate(bundle)
        bundle.obj.value = bundle.data['value']
        return bundle

    def get_object_list(self, request, filters={}):
        print filters
        results = []
        for value in PageValue.objects.filter(**filters):
            results.append(InfoValue(value))

        return results

    def obj_get_list(self, request=None, **kwargs):
        filters = {}

        if hasattr(request, 'GET'):
            # Grab a mutable copy.
            filters = request.GET.copy()

        # Update with the provided kwargs.
        filters.update(kwargs)

        applicable_filters = self.build_filters(filters=filters)
        print 'applicable', applicable_filters
        return self.get_object_list(request, filters=applicable_filters)

    def obj_get(self, request=None, **kwargs):
        value = PageValue.objects.get(**kwargs)
        return InfoValue(value)

    def obj_create(self, bundle, request=None, **kwargs):
        bundle = self.full_hydrate(bundle)
        obj = bundle.obj

        # Get the associated Attribute object.
        attribute = PageAttribute.objects.get(slug=obj.attribute)

        setattr(obj.page.eav, attribute.slug,
            to_attr_datatype(obj.value, attribute))

        obj.page.eav.save()

        return bundle

    def obj_update(self, bundle, request=None, **kwargs):
        # Same as create, because our create method updates in addition to
        # creating.
        return self.obj_create(bundle, request, **kwargs)

    def obj_delete(self, request=None, **kwargs):
        value = PageValue.objects.get(kwargs['pk'])
        value.delete()


class InfoAttributeResource(ModelResource):
    attribute = fields.CharField(attribute='slug')

    class Meta:
        queryset = PageAttribute.objects.all()
        resource_name = 'page_info_attribute'
        list_allowed_methods = ['get', 'post']

        excludes = [
            'slug', # hide slug because we re-introduce it as 'attribute'
            # created, modified aren't useful to expose.
            # searchable, display_in_list are useless right now, so hide
            # them.
            'created', 'modified', 'searchable', 'display_in_list']

        filtering = {
            'name': ALL,
            'attribute': ALL,
            'site': ALL_WITH_RELATIONS,
            'datatype': ALL,
            'required': ALL,
        }
        #authentication = ApiKeyWriteAuthentication()
        #authorization = ChangePageAuthorization() or ????
        authentication = Authentication()
        authorization = Authorization()


api.register(InfoResource())
api.register(InfoAttributeResource())
