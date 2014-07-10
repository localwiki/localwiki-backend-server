import datetime
import re

from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import Http404
from django.views.generic import date_based, list_detail
from django.db.models import Q
from django.conf import settings

from . models import *
from basic.tools.constants import STOP_WORDS_RE


def post_list(request, page=0, paginate_by=20, **kwargs):
    page_size = getattr(settings,'BLOG_PAGESIZE', paginate_by)
    return list_detail.object_list(
        request,
        queryset=Post.objects.published(),
        paginate_by=page_size,
        page=page,
        **kwargs
    )
post_list.__doc__ = list_detail.object_list.__doc__


def post_detail(request, slug, year, month, day, **kwargs):
    """
    Displays post detail. If user is superuser, view will display 
    unpublished post detail for previewing purposes.
    """
    posts = None
    if request.user.is_superuser:
        posts = Post.objects.all()
    else:
        posts = Post.objects.published()
    return date_based.object_detail(
        request,
        year=year,
        month=month,
        day=day,
        date_field='publish',
        slug=slug,
        queryset=posts,
        **kwargs
    )
post_detail.__doc__ = date_based.object_detail.__doc__
