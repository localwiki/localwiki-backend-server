from django.contrib.sitemaps import Sitemap
from models import Post


class BlogSitemap(Sitemap):
    priority = 0.5

    def items(self):
        return Post.objects.published()

    def lastmod(self, obj):
        return obj.publish
