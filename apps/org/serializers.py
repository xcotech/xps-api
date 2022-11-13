from rest_framework import serializers
from django.contrib.auth import get_user_model

from xps_cloud.serializers import BaseModelSerializer
from apps.org.models import *
from apps.system.models import System, Tag
from apps.system.serializers import SystemSerializer, TagSerializer
from apps.user.serializers import UserSerializer

class OrgSerializer(BaseModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(queryset=get_user_model().objects.all())

    class Meta:
        model = Org
        fields = (
            'id',
            'owner',
            'name',
            'description',
        )

class OrgSystemSerializer(BaseModelSerializer):
    org = serializers.PrimaryKeyRelatedField(queryset=Org.objects.all())
    system = serializers.PrimaryKeyRelatedField(queryset=System.objects.all())

    class Meta:
        model = OrgSystem
        fields = (
            'id',   
            'org',
            'system',
            'name',
            'description',
        )

    def to_representation(self, instance):
        representation = super(OrgSystemSerializer, self).to_representation(instance)
        representation['system'] = SystemSerializer(instance.system).data
        representation['org_obj'] = OrgMiniSerializer(instance.org).data
        return representation  



class OrgTagSerializer(BaseModelSerializer):
    org = serializers.PrimaryKeyRelatedField(queryset=Org.objects.all())
    tag = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all())
    # system = JSONSerializerField(write_only=True, required=False)

    class Meta:
        model = OrgTag
        fields = (
            'id',   
            'org',
            'tag'
        )

    def to_representation(self, instance):
        representation = super(OrgTagSerializer, self).to_representation(instance)
        representation['tag'] = TagSerializer(instance.tag).data
        representation['org_obj'] = OrgMiniSerializer(instance.org).data
        return representation  

class OrgMemberSerializer(BaseModelSerializer):
    org = serializers.PrimaryKeyRelatedField(queryset=Org.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=get_user_model().objects.all(), required=False)

    class Meta:
        model = OrgMember
        fields = (
            'id',
            'org',
            'user',
            'teams',
            'is_admin'
        )

    def to_representation(self, instance):
        from apps.user.serializers import UserSerializer
        from apps.org.utils import get_summary_stats

        representation = super(OrgMemberSerializer, self).to_representation(instance)
        representation['org_obj'] = OrgMiniSerializer(instance.org).data
        representation['stats'] = get_summary_stats(instance)
        representation['user'] = UserSerializer(instance.user).data

        return representation


class TeamSerializer(BaseModelSerializer):
    org = serializers.PrimaryKeyRelatedField(queryset=Org.objects.all())

    class Meta:
        model = Team
        fields = (
            'id',
            'org',
            'name',
            'description',
        )


class FeatureSerializer(BaseModelSerializer):
    class Meta:
        model = Feature
        fields = (
            'id',
            'name',
            'description',
            'status'
        )


class OrgFeatureSerializer(BaseModelSerializer):
    org = serializers.PrimaryKeyRelatedField(queryset=Org.objects.all())
    feature = serializers.PrimaryKeyRelatedField(queryset=Feature.objects.all())

    class Meta:
        model = OrgFeature
        fields = (
            'id',
            'org',
            'feature'
        )

    def to_representation(self, instance):
        representation = super(OrgFeatureSerializer, self).to_representation(instance)
        representation['feature'] = FeatureSerializer(instance.feature).data
        representation['org_obj'] = OrgMiniSerializer(instance.org).data
        return representation


class OrgMiniSerializer(BaseModelSerializer):
    cache_class = "mini"

    class Meta:
        model = Org
        fields = (
            'id',
            'name'
        )