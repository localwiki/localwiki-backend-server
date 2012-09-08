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
"""

from tastypie.resources import Resource
from tastypie import fields

from sapling.api.authentication import ApiKeyWriteAuthentication
from sapling.api.authorization import ChangePageAuthorization


class InfoResource(Resource):
    page = fields.ToOneField('pages.api.PageResource', 'page')

    class Meta:
        resource_name = 'page_info'
        authentication = ApiKeyWriteAuthentication()
        authorization = ChangePageAuthorization()
