import json
from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import JSONField, ArrayField
from django.db.models.signals import post_save

from model_utils import Choices

from xps_cloud.models import XPSModel

class Session(XPSModel):
    """
    A session is collection of activities belonging to an org
    """
    org = models.ForeignKey('org.Org', null=True, related_name='org_sessions', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    class Meta:
       ordering = ['-created']

    def __str__(self):
        return self.name        

    def can_admin(self, user):
        if user.is_staff:
            return True
        if self.org and self.org.can_admin(user):
            return True
        return False

class ActivityType(XPSModel):
    type_obj = JSONField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['type_obj'], name='unique_draft_user')
        ]

    def __str__(self):
        return f'Activity type {self.pk}'

    def can_admin(self, user):
        return True

class Activity(XPSModel):
    """
    An activity is an individual, single-user, standalone performance
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='activities', on_delete=models.SET_NULL, null=True)
    session = models.ForeignKey(Session, related_name='session_activities', on_delete=models.CASCADE)
    type_definition = models.ForeignKey(ActivityType, related_name='type_activities', null=True, on_delete=models.SET_NULL)
    labels = ArrayField(models.CharField(max_length=200), null=True, blank=True) # descriptive, labelling tags
    data_summary = JSONField(null=True, blank=True) # eg max_velocity, max_acceleration, total_time, reaction_time, height
    stats_type = models.CharField(max_length=255, blank=True, default='') # b64-encoded type_definition hash

    class Meta:
       ordering = ['-created']

    def __str__(self):
        return f'Activity {self.pk}'
        
    def get_type(self):
        return self.type_definition.type_obj

    def can_admin(self, user):
        return self.session.can_admin(user)
        

class ActivityData(XPSModel):
    """
    Raw recorded data, including derived events, for an individual activity.
    """
    activity = models.OneToOneField(Activity, related_name='data', on_delete=models.CASCADE, null=True)
    processed = models.DateTimeField(null=True, default=None)

    est_bak = JSONField(null=True, blank=True) # backup of incoming ests after normalization
    est = JSONField(null=True, blank=True) # time-series tracking/IMU data
    events = JSONField(null=True, blank=True) # all events recorded by the user application

    # for engingeering/debugging use
    tag_raw = JSONField(null=True, blank=True)
    tag_meas = JSONField(null=True, blank=True)
    control_response = JSONField(null=True, blank=True)
    control = JSONField(null=True, blank=True)
    system_config = JSONField(null=True, blank=True)
    hub_config = JSONField(null=True, blank=True)
    io_event = JSONField(null=True, blank=True)
    sensors = JSONField(null=True, blank=True)

    class Meta:
       ordering = ['-created']

    def __str__(self):
        return f'{self.activity.__str__()} Data'

    def can_admin(self, user):
        return self.activity.can_admin(user)

# def activity_data_post_save(sender, instance, created, **kwargs):
#     if not instance.processed:
#         try:
#             do_something(instance)
#         except Exception as e:
#             print(e)

# post_save.connect(activity_data_post_save, sender=ActivityData)


class ActivityFav(XPSModel):
    """
    Simple single-dimensional collection/favoriting model, 
    table of Activity models selecte by a specific User

    """
    activity = models.ForeignKey(Activity, related_name='fav_users', on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='favs', on_delete=models.SET_NULL, null=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-created'] 
        constraints = [
            models.UniqueConstraint(fields=['user','activity'], name='unique_user_favs')
        ]

    def __str__(self):
        return f'{self.activity.__str__()} Fav'

    def can_admin(self, user):
        return self.user == user

class ActivityAnnotation(XPSModel):
    """
    Allows users with permission to leave comments/annotations on an activity

    """
    activity = models.ForeignKey(Activity, related_name='annotations', on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='user_annotations', on_delete=models.SET_NULL, null=True)
    body = models.TextField(blank=True)
    admin = models.BooleanField(default=False, db_index=True) # admin-only flag

    class Meta:
        ordering = ['-created'] 
        constraints = []

    def __str__(self):
        return f'{self.activity.__str__()} Annotation'

    def can_admin(self, user):
        return self.activity.can_admin(user)

