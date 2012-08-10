from django.db import models
from pages.models import Page
import eav
from eav.registry import EavConfig
from eav.models import Attribute

eav.register(Page)