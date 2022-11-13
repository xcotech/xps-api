from django.db import models

from model_utils.models import TimeStampedModel
from xps_cloud.utils import invalidate


class XPSModel(TimeStampedModel, models.Model):
    sync_id = models.PositiveIntegerField(null=True)

    class Meta:
        abstract = True
        ordering = ['-created']

    def save(self, *args, **kwargs):
        super(XPSModel, self).save(*args, **kwargs)
        self.invalidate()

    def delete(self, *args, **kwargs):
        self.invalidate()
        super(XPSModel, self).delete(*args, **kwargs)

    def invalidate(self):
        invalidate(self)

    def can_admin(self, user):
        # in general, if the user is the user in this model, they can admin
        # otherwise, this should be overridden, or returns False
        try:
            return self.user == user
        except:
            return False