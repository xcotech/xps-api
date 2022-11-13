import random

from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.contrib.postgres.fields import JSONField
from xps_cloud.redis import RedisHash

from xps_cloud.models import XPSModel


class XPSUserManager(UserManager):
    """ Custom user manager to override/allow blank password """

    def add_user(self, **kwargs):
        password = kwargs.pop('password', 'changeme')

        user_fields = {}

        for attr in ['username', 'first_name', 'last_name', 'email']:
            user_fields[attr] = kwargs[attr] if attr in kwargs else ''
        user_fields['is_staff'] = False if not 'is_staff' in kwargs else kwargs['is_staff']

        if not 'username' in user_fields or not user_fields['username']:
            try:
                first_initial = user_fields['first_name'].lower()[0]
                last_name = user_fields['last_name'].lower().strip()
                random_num = random.randint(1,100000)
                user_fields['username'] = self.model.normalize_username(f'{first_initial}{last_name}_{random_num}')
            except:
                raise ValueError('The given username must be set')

        user_fields['email'] = self.normalize_email(user_fields['email'])
        user_fields['username'] = self.model.normalize_username(user_fields['username'])

        try:
            user = self.model(**user_fields)
        except Exception as e:
            print(e)
        
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
            user.is_active = False
        user.save(using=self._db)
        return user

class UserStatsCache(RedisHash):
    key_format = 'stats:user:%s'
    obj_id = -1

    # def __init__(self, user_id, redis=None):
    #     self.key = self.key_format
    #     self.init_redis(user_id, redis) 

class User(AbstractUser, XPSModel):
    """ Main user model - overrides the default, inherits from AbstractUser """
    bio = models.TextField(blank=True)

    # JWT for accessing XPS backend
    xps_token = models.CharField(max_length=255, null=True, default='')

    objects = XPSUserManager()

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
        ordering = ['-created']

    def __str__(self):
        return self.get_full_name()

    def get_org_member(self):
        return self.orgs.order_by('pk').first()

    def get_primary_org(self):
        try: 
            return self.orgs.order_by('pk').first().org
        except:
            pass
        return None

    @property
    def image_url(self):
        try:
            # TODO - change to load only the single primary image
            return self.images.first().s3_large_image
        except:
            # TODO - create our own here.
            return ''

    def thumbnail_url(self):
        try:
            # TODO - change to load only the single primary image
            return self.images.first().s3_small_image
        except:
            # TODO - create our own here.
            return ''

    def full_image_url(self):
        try:
            return f'{settings.S3_IMAGE_URL}/{settings.S3_IMAGE_FULL}/{self.images.first().public_id}'
        except:
            return ''

    def stats_cache(self):
        return UserStatsCache(self.pk)      

    def can_admin(self, user):
        if user.is_staff:
            return True
        return self == user

class UserImage(XPSModel):
    """ User profile images """
    user = models.ForeignKey(User, related_name='images', on_delete=models.CASCADE)

    primary = models.BooleanField(default=True)
    public_id = models.CharField(max_length=255)

    @property

    def s3_small_image(self):
        return f'{settings.S3_IMAGE_URL}/{settings.S3_IMAGE_SMALL}/{self.public_id}'

    def s3_large_image(self):
        return f'{settings.S3_IMAGE_URL}/{settings.S3_IMAGE_LARGE}/{self.public_id}'

    def s3_full_image(self):
        return f'{settings.S3_IMAGE_URL}/{settings.S3_IMAGE_FULL}/{self.public_id}'

    def __str__(self):
        return f'{self.user.get_full_name()}: Image(primary: {self.primary}) {self.pk}'

    def can_admin(self, user):
        return self.user.can_admin(user)
