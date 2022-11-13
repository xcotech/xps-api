from rest_framework import serializers

from apps.system.models import *
from apps.org.models import Org
from xps_cloud.serializers import BaseModelSerializer


class SystemSerializer(BaseModelSerializer):
    class Meta:
        model = System
        fields = ('id', 'serial_num', 'name', 'manufacture_date', 'build', 'wlan_ssid', 'hostname', 'wlan_password')

class TagSerializer(BaseModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'serial_num', 'name', 'manufacture_date', 'build')

class SystemBuildSerializer(BaseModelSerializer):
    class Meta:
        model = SystemBuild
        fields = ('id', 'name', 'description', 'build_date')

class TagBuildSerializer(BaseModelSerializer):
    class Meta:
        model = TagBuild
        fields = ('id', 'name', 'description', 'build_date')

class SystemLogSerializer(BaseModelSerializer):
    system = serializers.PrimaryKeyRelatedField(queryset=System.objects.all())

    class Meta:
        model = SystemEventLogEntry

        fields = (
            'system',
            'log_entry'
        )

    def create(self, validated_data):
        print('SystemLogSerializer.create.validated_data: %s' % validated_data)
        return SystemEventLogEntry.objects.create(**validated_data)


class HubFirmwareSerializer(BaseModelSerializer):
    class Meta:
        model = HubFirmware
        fields = ('id', 'name', 'fw', 'created')

    def create(self, validated_data):
        return HubFirmware.objects.create(**validated_data)

    def to_representation(self, instance):
        representation = super(HubFirmwareSerializer, self).to_representation(instance)
        representation['created'] = int(instance.created.timestamp() * 1e3)
        return representation  
