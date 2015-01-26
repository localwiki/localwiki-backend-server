from django.conf.urls.defaults import *

from django.views.generic.detail import DetailView
from django.views.generic.dates import ArchiveIndexView
from django.conf import settings

from .feeds import BlogPostsFeed
from .models import Post

class FullBodyFeed(BlogPostsFeed):
    def item_description(self, item):
        return item.body


class BlogListView(ArchiveIndexView):
    def get_queryset(self, *args, **kwargs):
        if self.request.user.is_superuser:
            return Post.objects.all()
        else:
            return Post.objects.published()


class BlogPageView(DetailView):
    def get_queryset(self, *args, **kwargs):
        if self.request.user.is_superuser:
            return Post.objects.all()
        else:
            return Post.objects.published()


urlpatterns = patterns('views',
    url(r'^(?P<year>\d{4})/(?P<month>\w{3})/(?P<day>\d{1,2})/(?P<slug>[-\w]+)/$',
        BlogPageView.as_view(),
        name='blog_detail'
    ),
    url(r'^$',
        BlogListView.as_view(paginate_by=settings.BLOG_PAGESIZE, date_field='publish', allow_future=False),
        name='blog_index',
    ),
    (r'^feed/$', FullBodyFeed()),

    # Hardcode this particular post
    # XXX INCLUDE THIS
    #(r'^2012/oct/10/localwiki-antarctica/', blog_antarctica),
)
