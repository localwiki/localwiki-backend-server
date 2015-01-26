from celery import shared_task

from django.utils.translation import ugettext as _
from django.db import models
from django.db.models.signals import post_save

from regions.models import Region


class RegionScore(models.Model):
    """
    A score assigned to a region that, roughly speaking, represents its
    quality.
    """
    region = models.OneToOneField(Region, related_name='score')
    score = models.PositiveIntegerField()

    def __unicode__(self):
        return _("Region score %s: %s" % (self.region, self.score))


def normalize_score(score):
    if score > 10000:
       score = 10000
    elif score > 4000:
       score = 5000
    elif score > 1000:
       score = 1000
    elif score > 100:
       score = 100
    elif score > 50:
       score = 50
    elif score > 30:
       score = 30
    elif score > 10:
       score = 10
    return score


@shared_task(ignore_result=True)
def _calculate_region_score(region_id):
    from maps.models import MapData
    from pages.models import Page, PageFile

    region = Region.objects.filter(id=region_id)
    if region.exists():
        region = region[0]
    else:
        return

    num_pages = Page.objects.filter(region=region).count()
    num_files = PageFile.objects.filter(region=region).count()
    num_maps = MapData.objects.filter(region=region).count()

    score = int(num_pages*1.5 + num_files*1.3 + num_maps)
    score = normalize_score(score)

    score_obj = RegionScore.objects.filter(region=region)
    if not score_obj.exists():
        score_obj = RegionScore(region=region)
    else:
        score_obj = score_obj[0]
    score_obj.score = score
    score_obj.save()

def _handle_region_score(sender, instance, created, raw, **kws):
    from pages.models import Page, PageFile
    from maps.models import MapData
    if raw:
        return
    if sender in [Page, MapData, PageFile]:
        _calculate_region_score.delay(instance.region.id)

post_save.connect(_handle_region_score)
