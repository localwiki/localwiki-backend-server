from django.db import models
from django.contrib.auth.models import User


class Event(models.Model):
    title = models.CharField(max_length=250)
    time_start = models.DateTimeField()
    location = models.CharField(max_length=250)
    description = models.TextField()
    posted_by = models.ForeignKey(User)
