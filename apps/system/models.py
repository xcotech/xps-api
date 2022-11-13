import datetime
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.contrib.postgres.fields import JSONField
from xps_cloud.models import XPSModel
from xps_cloud.utils import get_model_serial, get_hashid

class System(XPSModel):
    serial_num = models.CharField(null=True, max_length=255)
    name = models.CharField(max_length=255)
    
    wlan_ssid = models.CharField(null=True, max_length=255) # wlan ssid
    wlan_password = models.CharField(null=True, max_length=255) # wlan password
    hostname = models.CharField(null=True, max_length=255) # address of broker    

    manufacture_date = models.DateTimeField(null=True, default=None) # manufacture date for this instance
    build = models.ForeignKey('system.SystemBuild', related_name='build_systems', on_delete=models.SET_NULL, null=True)
    firmware = models.ForeignKey('system.HubFirmware', related_name='firmware_systems', on_delete=models.SET_NULL, null=True)

    class Meta:
       ordering = ['serial_num']

    def __str__(self):
        return self.serial_num

    def can_admin(self, user):
        if user.is_staff:
            return True
        return False

    def generate_serial(self):
        serial_values = []
        # content_type
        serial_values.append(ContentType.objects.get_for_model(self).pk)
        # build 
        serial_values.append(self.build.pk if self.build else 0)
        # system manufacture_date
        serial_values.append(int(datetime.datetime.timestamp(self.manufacture_date)*1000) if self.manufacture_date else 0)
        # system id
        serial_values.append(self.pk)
        return get_hashid(serial_values)

def system_post_save(sender, instance, created, **kwargs):
    if instance and not instance.serial_num:
        instance.serial_num = instance.generate_serial()
        if instance.serial_num:
            instance.save()

post_save.connect(system_post_save, sender=System)

class Tag(XPSModel):
    """
    A Tag is responsible for tracking an athlete and reporting data back to the system/hub
    """
    name = models.CharField(max_length=255) # for flexibility, name can be a number or string
    serial_num = models.CharField(null=True, max_length=255)

    manufacture_date = models.DateTimeField(null=True, default=None) # manufacture date for this instance
    build = models.ForeignKey('system.TagBuild', related_name='build_tags', on_delete=models.SET_NULL, null=True)
    firmware = models.ForeignKey('system.TagFirmware', related_name='firmware_tags', on_delete=models.SET_NULL, null=True)

    class Meta:
       ordering = ['name']

    def __str__(self):
        return f'Tag: {self.serial_num}'

    def generate_serial(self):
        serial_values = []
        # content_type
        serial_values.append(ContentType.objects.get_for_model(self).pk)
        # build 
        serial_values.append(self.build.pk if self.build else 0)
        # system manufacture_date
        serial_values.append(int(datetime.datetime.timestamp(self.manufacture_date)*1000) if self.manufacture_date else 0)
        # system id
        serial_values.append(self.pk)
        return get_hashid(serial_values)

def tag_post_save(sender, instance, created, **kwargs):
    if instance and not instance.serial_num:
        instance.serial_num = instance.generate_serial()
        if instance.serial_num:
            instance.save()

post_save.connect(tag_post_save, sender=Tag)

class SystemBuild(XPSModel):
    """
    Build/revision details for a specific batch of systems (ie hubs)
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    build_date = models.DateTimeField(null=True, default=None)

    class Meta:
       ordering = ['build_date', 'created']

    def __str__(self):
        return f'SystemBuild {self.pk}'

    def can_admin(self, user):
        if user.is_staff:
            return True
        return False

class TagBuild(XPSModel):
    """
    Build/revision details for a specific batch of tags
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    build_date = models.DateTimeField(null=True, default=None)

    class Meta:
       ordering = ['build_date', 'created']

    def __str__(self):
        return f'TagBuild {self.pk}'

    def can_admin(self, user):
        if user.is_staff:
            return True
        return False

class SystemEventLogEntry(XPSModel):
    """
    Generic log for system/application events that are worth noting
    """
    system = models.ForeignKey('system.System', related_name='log_entries', on_delete=models.SET_NULL, null=True)
    log_entry = JSONField(null=True, blank=True)

    class Meta:
       ordering = ['-created']

    def __str__(self):
        return self.pk

    def can_admin(self, user):
        return True

class HubFirmware(XPSModel):
    """
    Firmware that may be applied to an XPS System
    """
    name = models.CharField(null=True, max_length=255)
    version = models.CharField(null=True, max_length=255)
    fw = models.FileField(blank=True, default='', upload_to='assets/firmware/hub/')

    class Meta:
       ordering = ['-created']

    def can_admin(self, user):
        return True if user.is_staff else False

    def __str__(self):
        return f'HubFirmware {self.pk}'

class TagFirmware(XPSModel):
    """
    Firmware that may be applied to an XPS tracking tag
    """
    name = models.CharField(null=True, max_length=255)
    version = models.CharField(null=True, max_length=255)
    fw = models.FileField(blank=True, default='', upload_to='assets/firmware/tag/')

    class Meta:
       ordering = ['-created']

    def can_admin(self, user):
        return True if user.is_staff else False

    def __str__(self):
        return f'TagFirmware {self.pk}'