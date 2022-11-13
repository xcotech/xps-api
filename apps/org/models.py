from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.contrib.postgres.fields import JSONField
from xps_cloud.models import XPSModel
from apps.org.utils import get_summary_stats

class Org(XPSModel):
    """
    An Org represents a company/customer
    """
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='orgs_created', null=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    class Meta:
       ordering = ['name']

    def __str__(self):
        return self.name

    def can_admin(self, user):
        if self.owner == user:
            return True
        return user.get_org_member().org == self

def org_post_save(sender, instance, created, **kwargs):
    if instance and created:
        # create an OrgMember model for the "owner"
        OrgMember.objects.create(org=instance, user=instance.owner, is_admin=True)

post_save.connect(org_post_save, sender=Org)

class Team(XPSModel):
    """
    A team (optionally) within an organization
    """
    org = models.ForeignKey(Org, related_name='teams', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    # catchall = models.BooleanField(default=False, db_index=True) #  

    class Meta:
       ordering = ['name']

    def __str__(self):
        return f'{self.org.name}: {self.name}'

    def can_admin(self, user):
        return self.org.can_admin(user)
        
class OrgSystem(XPSModel):
    """
    System accessible to a given Org
    """
    org = models.ForeignKey(Org, related_name='systems', on_delete=models.CASCADE)
    system = models.ForeignKey('system.System', related_name='orgs', on_delete=models.CASCADE)

    name = models.CharField(blank=True, max_length=255)
    description = models.TextField(blank=True)

    class Meta:
       ordering = ['name']
       unique_together = ('org', 'system')

    def __str__(self):
        return self.name

    def can_admin(self, user):
        return self.org.can_admin(user)        

class OrgTag(XPSModel):
    """
    Tag accessible to a given Org
    """
    org = models.ForeignKey(Org, related_name='tags', on_delete=models.CASCADE)
    tag = models.ForeignKey('system.Tag', related_name='orgs', on_delete=models.CASCADE)

    class Meta:
       ordering = ['tag__serial_num']

    def __str__(self):
        return self.tag.name

    def can_admin(self, user):
        return self.org.can_admin(user)        

class OrgMember(XPSModel):
    """
    An athlete, or a member of an org/company/school.
    """
    org = models.ForeignKey(Org, related_name='members', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='orgs', on_delete=models.CASCADE)
    # can this user administer this org?
    is_admin = models.BooleanField(default=False, db_index=True)

    # current tag set on this athlete
    current_tag = models.ForeignKey('system.Tag', null=True, on_delete=models.SET_NULL)
    teams = models.ManyToManyField(Team, related_name='members', blank=True)
    permissions = models.ManyToManyField('org.Permission', related_name='permission_org_members')

    class Meta:
       ordering = ['org__name', 'user__last_name', 'user__first_name']
       unique_together = ('org', 'user')

    def __str__(self):
        return f'{self.org.name}: {self.user.get_full_name()}'

    def has_permission(self, permission_name):
        return True if self.permissions.filter(name=permission_name) else False

    def can_admin(self, user):
        return self.org.can_admin(user)        

    def get_summary_stats(self):
        return get_summary_stats(self)

class Permission(XPSModel):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)

    '''
    example permissions:
    -------------------
    IsStaff: user is a member of XCO staff
    FullAdmin: user has effective sueperuser/admin privileges
    OrgCanAdmin: user is able to administer (update, delete) Org 
    OrgSessionsCanAdmin: user is able to administer Sessions within an Org
    '''

    def __str__(self):
        return f'{self.name}'

class OrgMemberPermission(XPSModel):
    org_member = models.ForeignKey(OrgMember, related_name='org_member_permissions', on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, related_name='permission_org_member_permissions', on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.name}: {self.org_member.pk}'


class Feature(XPSModel):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    status = models.CharField(max_length=255, blank=True)

    '''
    example features:
    -------------------
    walking: Enable Walking mode in Sprint
    '''

    def __str__(self):
        return f'{self.name}'

    def can_admin(self, user):
        return user.is_staff


class OrgFeature(XPSModel):
    """
    Feature accessible to a given Org
    """
    org = models.ForeignKey(Org, related_name='features', on_delete=models.CASCADE)
    feature = models.ForeignKey('Feature', related_name='orgs', on_delete=models.CASCADE)

    class Meta:
       ordering = ['feature__name']

    def __str__(self):
        return self.feature.name

    def can_admin(self, user):
        return self.org.can_admin(user)
