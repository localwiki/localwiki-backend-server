import os

DEBUG = False


# Set Django debug mode based on environment variable
DEBUG = os.getenv('DJANGO_DEBUG', DEBUG)
if DEBUG: DEBUG = True

#######################################################################
# Config values you *must* change
######################################################################

ALLOWED_HOSTS = ['.{{ public_hostname }}', {% for hostname in custom_domains %}'{{ hostname }}', {% endfor %} '127.0.0.1', '.localhost']

SESSION_COOKIE_DOMAIN = '.{{ public_hostname }}'
if SESSION_COOKIE_DOMAIN.endswith('.localhost'):
    SESSION_COOKIE_DOMAIN = None

MAIN_HOSTNAME = '{{ public_hostname }}'
CUSTOM_HOSTNAMES = [{% for hostname in custom_domains %}'{{ hostname }}', {% endfor %}]
XSESSION_DOMAINS = [{% for hostname in custom_domains %}'{{ hostname }}', {% endfor %}'{{ public_hostname }}']

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'localwiki',
        'USER': 'localwiki',
        'PASSWORD': '{{ postgres_db_pass }}',
        'HOST': '127.0.0.1',
    }
}

# For testing, you can start the python debugging smtp server like so:
# sudo python -m smtpd -n -c DebuggingServer localhost:25
EMAIL_HOST = 'localhost'
EMAIL_HOST_PASSWORD = ''
EMAIL_PORT = 25
EMAIL_USE_TLS = False
DEFAULT_FROM_EMAIL = 'dontreply@{{ public_hostname }}'

# For Sentry error logging
RAVEN_CONFIG = {
    'dsn': '{{ sentry_secret_url }}',
}

#######################################################################
# Other config values.
#######################################################################

OLWIDGET_CUSTOM_LAYER_TYPES = {
    'mblw': """OpenLayers.Layer.XYZ('MB LW',
        ["http://a.tiles.mapbox.com/v3/philipn.hjmo8m80/${z}/${x}/${y}.png"], {
            sphericalMercator: true,
            wrapDateLine: true,
    })""",
}

DAISYDIFF_URL = 'http://localhost:8080/daisydiff/diff'
DAISYDIFF_MERGE_URL = 'http://localhost:8080/daisydiff/merge'

# list of regular expressions for white listing embedded URLs
EMBED_ALLOWED_SRC = ['.*']

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.solr_backend.SolrEngine',
        'URL': 'http://localhost:8080/solr/',
    }
}

BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    'django.template.loaders.eggs.Loader',
#     'django.template.loaders.eggs.load_template_source',
)

if '':
    LOCAL_INSTALLED_APPS = (
        'raven.contrib.django.raven_compat',
    )
else:
    LOCAL_INSTALLED_APPS = (
        'profiler',
    )

if DEBUG:
     LOCAL_MIDDLEWARE_CLASSES = (
        'armstrong.esi.middleware.IncludeEsiMiddleware',
     )
else:
    LOCAL_MIDDLEWARE_CLASSES = ()
    TEMPLATE_LOADERS = (('django.template.loaders.cached.Loader', TEMPLATE_LOADERS),)

POSTGIS_VERSION = (2, 0, 3)

CACHES = {
    'default': {
        'BACKEND': 'johnny.backends.memcached.MemcachedCache',
        'KEY_PREFIX': '',
	    'LOCATION': '127.0.0.1:11211',
        'JOHNNY_CACHE': True,
    },
    'long-living': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'django_db_cache_table',
        'TIMEOUT': 60 * 60 * 24 * 365 * 2,  # 2 years
        'OPTIONS': {
            'MAX_ENTRIES': 500000,  # A nice big number. ~2GB of in-DB space used.
            'CULL_FREQUENCY': 30,
        }
    }
}

SECRET_KEY = '{{ django_secret_key }}'

SENTRY_REMOTE_URL = 'https://errors.localwiki.org/sentry/store/'
SENTRY_KEY = '{{ sentry_key }}'
