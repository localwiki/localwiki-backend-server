from django.db import models
from pages.models import Page
import eav
from eav.registry import EavConfig
from eav.models import Attribute


class PageEavConfig(EavConfig):
    '''
    Class that determines the attributes that apply to a Page.
    '''
    @classmethod
    def get_attributes(cls, entity=None):
        '''
        By default, all :class:`~eav.models.Attribute` object apply to an
        entity, unless you provide a custom EavConfig class overriding this.
        '''
        qs = super(PageEavConfig, cls).get_attributes(entity)
        # TODO: filter just ones for this page instance? 
        return qs


eav.register(Page, PageEavConfig)