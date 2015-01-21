import django
from django.db.models.loading import AppCache

django_apps_loaded = django.dispatch.Signal()

def populate_with_signal(cls):
    ret = cls._populate_orig()
    if cls.app_cache_ready():
        if not hasattr(cls, '__signal_sent'):
            cls.__signal_sent = True
            django_apps_loaded.send(sender=None)
    return ret

if not hasattr(AppCache, '_populate_orig'):
    AppCache._populate_orig = AppCache._populate
    AppCache._populate = populate_with_signal


class MultiQuerySet(object):
    def __init__(self, *args, **kwargs):
        self.querysets = args
        self._count = None
        self.model = args[0].model
    
    def count(self):
        if not self._count:
            self._count = sum(len(qs) for qs in self.querysets)
        return self._count
    
    def __len__(self):
        return self.count()
        
    def __getitem__(self, item):
        indices = (offset, stop, step) = item.indices(self.count())
        items = []
        total_len = stop - offset
        for qs in self.querysets:
            if len(qs) < offset:
                offset -= len(qs)
            else:
                items += list(qs[offset:stop])
                if len(items) >= total_len:
                    return items
                else:
                    offset = 0
                    stop = total_len - len(items)
                    continue



from django.template import add_to_builtins
add_to_builtins('utils.templatetags.smart_url')
