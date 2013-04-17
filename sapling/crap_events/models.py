from django.db import models
from django.contrib.auth.models import User

from ckeditor.models import HTML5FragmentField


class Event(models.Model):
    title = models.CharField(max_length=250)
    time_start = models.DateTimeField()
    location = models.CharField(max_length=250)
    description = models.TextField()
    posted_by = models.ForeignKey(User)
    
    class Meta:
        ordering = ['time_start']
