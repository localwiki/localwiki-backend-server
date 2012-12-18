""" Ideal infobox API interaction:

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


Filtering on custom values-

How would we find all places open between 5 and 6pm on Wednesday?

/info/?
    hours_open__day=wednesday&
    hours_open__start_time__gte=5pm&
    hours_open__end_time__gte=6pm


new types could be required to register with tastypie

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

from models import PageAttribute, PageValue, WeeklyTimeBlock, WeeklySchedule


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
]


def to_attr_type(o, attribute):
    """
    Args:
        o: a JSON-like object.
        attribute: an Attribute instance.

    Returns:
        o cast to the type of the provided attribute.
    """
    # TODO: A way to easily extend this when adding new data types.
    if attribute.type in AUTOMATIC_DATATYPES:
        return o

    if attribute.type == PageAttribute.TYPE_DATE:
        f = fields.DateTimeField()
        return f.convert(o)

    if attribute.type == PageAttribute.TYPE_SCHEDULE:
        pass

    raise TypeError("The type %s is not supported via the API yet" %
        attribute.type)


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
    # We manage the setting/getting of 'value' by hand, but we'll set
    # value to a CharField here just to add 'value' as a concrete field.
    # This is needed in build_filters().
    # XXX TODO: remove this nonsense once we're using /info/?has_wifi=True
    # style & not using build_filters as a mixin
    value = fields.CharField(attribute='value')

    class Meta:
        resource_name = 'page_info'
        object_class = InfoValue
        list_allowed_methods = ['get', 'post']
        filtering = {
            'attribute': ALL,
            'value': ALL_WITH_RELATIONS,
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
        # XXX TODO: remove this nonsense once we're using /info/?has_wifi=True
        # style & not using build_filters as a mixin

        # We use 'attribute' as a shortcut for 'attribute.slug', so let's sub
        # that in here.
        slug = filters.get('attribute__exact')
        if slug:
            filters['attribute__slug'] = filters['attribute__exact']
            del filters['attribute__exact']

            # use attribute type to get value type         
            attribute = PageAttribute.objects.get(slug=slug)
            type = attribute.type

        for k in filters.keys():
            if k.startswith('value__'):
                # The 'value' attribute is actually one of many possible
                # value types (value_text, value_date, etc).  So we use
                # the type of the attribute to determine which to
                # map this to.
                rest = k[7:]  # len 'value__' = 7
                value = to_attr_type(filters[k], attribute)
                filters['value_%s__%s' % (type, rest)] = value
                del filters[k]

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
            to_attr_type(obj.value, attribute))

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
            'type': ALL,
            'required': ALL,
        }
        #authentication = ApiKeyWriteAuthentication()
        #authorization = ChangePageAuthorization() or ????
        authentication = Authentication()
        authorization = Authorization()


class WeeklyTimeBlockResource(ModelResource):
    class Meta:
        queryset = WeeklyTimeBlock.objects.all()
        resource_name = 'page_info_weekly_time_block'
        filtering = {
            'start_time': ALL,
            'end_time': ALL,
            'week_day': ALL,
        }


class WeeklyScheduleResource(ModelResource):
    time_blocks = fields.ToManyField('infobox.api.WeeklyTimeBlockResource',
        'time_blocks', full=True)

    class Meta:
        queryset = WeeklySchedule.objects.all()
        resource_name = 'page_info_weekly_schedule'
        filtering = {
            'time_blocks': ALL_WITH_RELATIONS,
        }

        #authentication = ApiKeyWriteAuthentication()
        #authorization = ChangePageAuthorization() or ????
        authentication = Authentication()
        authorization = Authorization()


# Allow filtering on all fields of PageValue.  We construct this
# dynamically because of all the possible value_* fields.
FILTERING_FIELDS = {}
for f in PageValue._meta.fields:
    FILTERING_FIELDS[f.name] = ALL_WITH_RELATIONS


class InfoValueResource(ModelResource):
    attribute = fields.ForeignKey(InfoAttributeResource, 'attribute', full=True)
    value_schedule = fields.ToOneField(WeeklyScheduleResource,
        'value_schedule', null=True, full=True)

    class Meta:
        queryset = PageValue.objects.all()
        resource_name = 'page_info_value'
        list_allowed_methods = ['get', 'post']

        filtering = FILTERING_FIELDS

        #authentication = ApiKeyWriteAuthentication()
        #authorization = ChangePageAuthorization() or ????
        authentication = Authentication()
        authorization = Authorization()

    def dehydrate(self, bundle):
        # Over-ride 'attribute' to be just the attribute slug for easy-of-use.
        bundle.data['attribute'] = bundle.obj.attribute.slug
        bundle.data['type'] = bundle.obj.attribute.type

        datatype = bundle.obj.attribute.type
        bundle.data['value'] = bundle.data['value_%s' % datatype]
        # Hide all other value_ fields
        for field in bundle.data.keys():
            if field.startswith('value_'):
                del bundle.data[field]

        return bundle

    def full_hydrate(self, bundle):
        bundle = super(InfoValueResource, self).full_hydrate(bundle)

        # Over-ride 'attribute' to be just the attribute slug for easy-of-use.
        attribute = PageAttribute.objects.get(attribute=bundle.data['attribute'])
        bundle.obj.attribute = attribute

        # Take the provided 'value' and stuff it into the associated
        # 'value_<type>' field.
        # XXX TODO
        raise Exception

        return bundle

    def build_filters(self, filters=None):
        # Because we over-ride 'attribute' we need to set it to the
        # correct, deeper lookup here.
        if filters.get('attribute'):
            slug = filters['attribute']
            filters['attribute__attribute'] = slug
            del filters['attribute']
            attribute = PageAttribute.objects.get(slug=slug)
            datatype = attribute.type

        # Because we over-ride 'type' we need to set it to the correct,
        # deeper lookup here.
        if filters.get('type'):
            datatype = filters['type']
            filters['attribute__type'] = datatype
            del filters['type']

        for k in filters.keys():
            # Set the generic 'value' filter to the correct type value.
            if k.startswith('value'):
                rest = k[5:]  # len('value') == 5
                filters['value_%s%s' % (datatype, rest)] = filters[k]
                del filters[k]

        return super(InfoValueResource, self).build_filters(filters)


api.register(InfoResource())
api.register(InfoAttributeResource())

api.register(WeeklyTimeBlockResource())
api.register(WeeklyScheduleResource())

api.register(InfoValueResource())
