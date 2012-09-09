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


"""

from tastypie.resources import Resource, Bundle
from tastypie import fields

from eav.models import Attribute, Value

from sapling.api import api
from sapling.api.authentication import ApiKeyWriteAuthentication
from sapling.api.authorization import ChangePageAuthorization


class InfoValue(object):
    def __init__(self, value):
        self.value = value
        self.attribute = self.value.attribute.slug
        self.page = self.value.entity


class InfoResource(Resource):
    attribute = fields.CharField(attribute='attribute')
    page = fields.ToOneField('pages.api.PageResource', 'page')

    class Meta:
        resource_name = 'page_info'
        object_class = InfoValue
        authentication = ApiKeyWriteAuthentication()
        authorization = ChangePageAuthorization()

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}

        if isinstance(bundle_or_obj, Bundle):
            kwargs['pk'] = bundle_or_obj.obj.value.id
        else:
            kwargs['pk'] = bundle_or_obj.value.id

        return kwargs

    def dehydrate(self, bundle):
        bundle.data['value'] = bundle.obj.value.value
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
        # How do we turn the kwargs into the right thing here?
        bundle.obj = InfoValue(initial=kwargs)
        bundle = self.full_hydrate(bundle)

        # create new Value here, potentially create new Attribute as
        # well.  Tie it to the page
        pass

        return bundle

    def obj_update(self, bundle, request=None, **kwargs):
        return self.obj_create(bundle, request, **kwargs)

    def obj_delete_list(self, request=None, **kwargs):
        bucket = self._bucket()

        for key in bucket.get_keys():
            obj = bucket.get(key)
            obj.delete()

    def obj_delete(self, request=None, **kwargs):
        value = Value.objects.get(kwargs['pk'])
        value.delete()


api.register(InfoResource())
