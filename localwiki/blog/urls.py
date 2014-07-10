from django.conf.urls.defaults import *

from django.views.generic.detail import DetailView
from django.views.generic.dates import ArchiveIndexView
from django.conf import settings

from .feeds import BlogPostsFeed
from .models import Post

qs = Post.objects.all()

class FullBodyFeed(BlogPostsFeed):
    def item_description(self, item):
        return item.body


urlpatterns = patterns('views',
    url(r'^(?P<year>\d{4})/(?P<month>\w{3})/(?P<day>\d{1,2})/(?P<slug>[-\w]+)/$',
        DetailView.as_view(queryset=qs),
        name='blog_detail'
    ),
    url(r'^$',
        ArchiveIndexView.as_view(queryset=qs, paginate_by=settings.BLOG_PAGESIZE, date_field='publish', allow_future=False),
        name='blog_index',
    ),
    (r'^feed/$', FullBodyFeed()),

    # Hardcode this particular post
    # XXX INCLUDE THIS
    #(r'^2012/oct/10/localwiki-antarctica/', blog_antarctica),
)
