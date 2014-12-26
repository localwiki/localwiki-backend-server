from django.db.models.signals import post_save, post_delete

from .models import MapData
from .cache import _map_cache_post_save, _map_cache_pre_delete


post_save.connect(_map_cache_post_save, sender=MapData)
post_delete.connect(_map_cache_pre_delete, sender=MapData)
