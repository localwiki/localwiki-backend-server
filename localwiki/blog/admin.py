from django.contrib import admin

from . models import Post


class PostAdmin(admin.ModelAdmin):
    list_display  = ('title', 'publish', 'status')
    list_filter   = ('publish', 'status')
    search_fields = ('title', 'body')
    prepopulated_fields = {'slug': ('title',)}
admin.site.register(Post, PostAdmin)
