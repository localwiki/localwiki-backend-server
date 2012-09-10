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
from tastypie.authentication import Authentication
from tastypie.authorization import Authorization

from eav.models import Attribute, Value

from sapling.api import api
from sapling.api.authentication import ApiKeyWriteAuthentication
from sapling.api.authorization import ChangePageAuthorization


class InfoValue(object):
    def __init__(self, value=None):
        if value is None:
            return

        self.id = value.id
        self.value = value
        self.attribute = self.value.attribute.slug
        self.page = self.value.entity


AUTOMATIC_DATATYPES = [
    Attribute.TYPE_TEXT,
    Attribute.TYPE_FLOAT,
    Attribute.TYPE_INT,
    Attribute.TYPE_BOOLEAN,
    Attribute.TYPE_BOOLEAN,
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

    if attribute.datatype is Attribute.TYPE_DATE:
        f = fields.DateTimeField()
        return f.convert(o)

    raise TypeError("The datatype %s is not supported via the API yet" %
        attribute.datatype)


class InfoResource(Resource):
    id = fields.IntegerField(attribute='id')
    attribute = fields.CharField(attribute='attribute')
    page = fields.ToOneField('pages.api.PageResource', 'page')

    class Meta:
        resource_name = 'page_info'
        object_class = InfoValue
        #authentication = ApiKeyWriteAuthentication()
        #authorization = ChangePageAuthorization()
        authentication = Authentication()
        authorization = Authorization()

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}

        if isinstance(bundle_or_obj, Bundle):
            obj = bundle_or_obj.obj
            attribute = Attribute.objects.get(slug=obj.attribute)
            value = Value.objects.get(entity=obj.page, attribute=attribute)
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

    def get_object_list(self, request):
        results = []
        for value in Value.objects.all():
            results.append(InfoValue(value))

        return results

    def obj_get_list(self, request=None, **kwargs):
        # Filtering disabled for brevity...
        return self.get_object_list(request)

    def obj_get(self, request=None, **kwargs):
        value = Value.objects.get(**kwargs)
        return InfoValue(value)

    def obj_create(self, bundle, request=None, **kwargs):
        bundle = self.full_hydrate(bundle)
        obj = bundle.obj

        # Get the associated Attribute object.
        attribute = Attribute.objects.get(slug=obj.attribute)

        setattr(obj.page.eav, attribute.slug,
            to_attr_datatype(obj.value, attribute))

        obj.page.eav.save()

        return bundle

    def obj_update(self, bundle, request=None, **kwargs):
        # Same as create, because our create method updates in addition to
        # creating.
        return self.obj_create(bundle, request, **kwargs)

    def obj_delete_list(self, request=None, **kwargs):
        bucket = self._bucket()

        for key in bucket.get_keys():
            obj = bucket.get(key)
            obj.delete()

    def obj_delete(self, request=None, **kwargs):
        value = Value.objects.get(kwargs['pk'])
        value.delete()


class InfoAttributeResource(ModelResource):
    attribute = fields.CharField(attribute='slug')

    class Meta:
        queryset = Attribute.objects.all()
        resource_name = 'page_info_attribute'
        list_allowed_methods = ['get', 'post']

        excludes = [
            'slug', # hide slug because we re-introduce it as 'attribute'
            # created, modified aren't useful to expose.
            # searchable, display_in_list are useless right now, so hide
            # them.
            'created', 'modified', 'searchable', 'display_in_list']

        filtering = {
            'attribute': ALL,
        }
        #authentication = ApiKeyWriteAuthentication()
        #authorization = ChangePageAuthorization() or ????
        authentication = Authentication()
        authorization = Authorization()


api.register(InfoResource())
api.register(InfoAttributeResource())
