import json
from django.contrib.auth import get_user_model

from rest_framework import serializers
from xps_cloud.serializers import JSONSerializerField, BaseModelSerializer
from .models import *
from apps.system.models import Tag


class UserImageSerializer(BaseModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=get_user_model().objects.all())

    class Meta:
        model = UserImage
        fields = (
            'id',
            'user',
            'primary',
            'public_id',
            's3_large_image',
            's3_small_image',
            's3_full_image',
        )

class UserSerializer(BaseModelSerializer):
    cache_class = "item"
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    username = serializers.CharField(required=False)
    password = serializers.CharField(required=False, write_only=True)

    class Meta:
        model = get_user_model()
        fields = (
            'id',
            'username',
            'email',
            'full_name',
            'first_name',
            'last_name',
            'bio',
            'is_staff',
            'image_url',
            'full_image_url',
            'thumbnail_url',
            'is_staff',
            'password'
        )
        read_only_fields = ('image_url', 'thumbnail_url', 'full_image_url')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password') if 'password' in validated_data else ''
        user = get_user_model().objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def to_representation(self, instance):
        from apps.org.serializers import OrgSerializer, OrgMemberSerializer
        representation = super(UserSerializer, self).to_representation(instance)
        
        try:
            org_member_primary = instance.orgs.first()
            representation['org_member'] = org_member_primary.pk # org_member.pk
            representation['org'] = { 'admin': org_member_primary.is_admin, **OrgSerializer(org_member_primary.org).data}
        except:
            pass

        return representation

class UserMiniSerializer(BaseModelSerializer):
    cache_class = "mini"
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = get_user_model()
        fields = (
            'id',
            'full_name',
            'image_url',
            'full_image_url',
            'thumbnail_url'
        )