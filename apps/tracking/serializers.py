import base64, json
from django.contrib.auth import get_user_model
from rest_framework import serializers

from xps_cloud.serializers import JSONSerializerField, BaseModelSerializer
from apps.tracking.models import *
from apps.system.models import *
from apps.org.models import Org
from apps.user.serializers import UserSerializer, UserMiniSerializer
from xps_cloud.utils import api_serialize

class SessionSerializer(BaseModelSerializer):
    created = serializers.DateTimeField(required=False)
    org = serializers.PrimaryKeyRelatedField(queryset=Org.objects.all())
    sync_id = serializers.IntegerField(max_value=None, min_value=None, required=False)

    class Meta:
        model = Session
        fields = (
            'id',
            'org',
            'name',
            'description',
            'sync_id',
            'created',
            'modified'
        )

    def create(self, validated_data):
        # check for a previously synced model        
        synced = self.check_synced(validated_data)
        if synced:
            return synced        

        force_created = validated_data.pop('created', None)
        session = Session.objects.create(**validated_data)

        if force_created:
            session.created = force_created
            session.save()
        return session

class ActivityDataSerializer(BaseModelSerializer):
    activity = serializers.PrimaryKeyRelatedField(queryset=Activity.objects.all())

    class Meta:
        model = ActivityData
        fields = (
            # 'id', # lopping this off because we want to fetch ActivityData (OneToOne) activity.pk
            'activity',
            'est',
            'sensors',
            'tag_raw',
            'control_response',
            'control',
            'system_config',
            'tag_meas',
            'est_bak',
            'io_event',
            'events'
            )

    def create(self, validated_data):
        return ActivityData.objects.create(**validated_data)

    def to_representation(self, instance):
        representation = super(ActivityDataSerializer, self).to_representation(instance)

        try:
            velocity_ranges = json.loads(instance.activity.user.stats_cache().get('velocity_ranges'))
            if velocity_ranges:
                representation['user_velocity_ranges'] = velocity_ranges
        except:
            pass

        # request = self.context.get('request', None)
        # get_all = True if request and 'all' in request.query_params else False

        # if get_all:
        #     representation['tag_raw'] = instance.tag_raw
        #     representation['sensors'] = instance.sensors
        #     representation['tag_meas'] = instance.tag_meas
        #     representation['control_response'] = instance.control_response
        #     representation['control'] = instance.control
        #     representation['system_config'] = instance.system_config
        #     representation['hub_config'] = instance.hub_config

        return representation

class RoundingDecimalField(serializers.DecimalField):
    """Used to automaticaly round decimals to the model's accepted value."""
    def validate_precision(self, value):
        return value

class ActivityTypeSerializer(BaseModelSerializer):
    ''' Serializer built to normalize an activity's type/attrs object '''
    type_obj = JSONSerializerField(required=True)
   
    class Meta:
        model = ActivityType
        fields = (
            'id',
            'type_obj'
            )

    def normalize_activity_type(self, type_attrs):
        ''' normalize attrs object: we want to get or create based on a constrained
        attributes object describing in only essential detail a particular type of activity '''        
        target_type_attributes = {
            "sprint": ['activity_type', 'units', 'distance', 'start_type', 'direction', 'side', 'skating', 'bobsled', 'walking'],
            "agility": ['activity_type', 'units', 'distance', 'start_type', 'agility_type', 'agility_cuts', 'agility_angle'],
            "jump": ['activity_type', 'units', 'orientation', 'direction', 'side', 'triple_jump_type'],
            "freeform": ['activity_type', 'units'],
            "eng": ['activity_type', 'units']
        }

        normalized_attrs = {}
        activity_type = type_attrs.get('activity_type', None)
        
        if activity_type:
            for field, value in type_attrs.items():
                try:
                    value = None if not field in target_type_attributes.get(activity_type, None) else value
                except Exception as e:
                    print(e)
                normalized_attrs[field] = value
            if normalized_attrs:
                normalized_attrs = {k: v for k, v in normalized_attrs.items() if v is not None} # strip out empty keys

        return normalized_attrs

    def create(self, validated_data):
        # print('normalized type def: %s' % self.normalize_activity_type(validated_data.get('type_obj', None)))
        activity_type, created = ActivityType.objects.get_or_create(type_obj=self.normalize_activity_type(validated_data.get('type_obj', None)))
        # print('NOT CREATED' if not created else 'CREATED')
        return activity_type

class ActivitySerializer(BaseModelSerializer):
    created = serializers.DateTimeField(required=False)
    session = serializers.PrimaryKeyRelatedField(queryset=Session.objects.all(), required=False)
    user = serializers.PrimaryKeyRelatedField(queryset=get_user_model().objects.all())
    type_definition = serializers.PrimaryKeyRelatedField(queryset=ActivityType.objects.all(), required=True)
    labels = serializers.ListField(child=serializers.CharField(), required=False)
    data_summary = JSONSerializerField(required=False)
    sync_id = serializers.IntegerField(max_value=None, min_value=None, required=False)
    data = JSONSerializerField(write_only=True, required=False)
    stats_type = serializers.CharField(required=False)

    class Meta:
        model = Activity
        fields = (
            'id',
            'session',
            'user',
            'type_definition',
            'labels',
            'data_summary',                      
            'data',
            'sync_id',
            'stats_type',
            'created'
        )

    def create(self, validated_data): 
        # check for a previously synced model        
        synced = self.check_synced(validated_data)
        if synced:
            return synced

        data = validated_data.pop('data') if 'data' in validated_data else {}
        created_time = validated_data.pop('created', None)

        if hasattr(data, 'events'):
            if not hasattr(validated_data, 'data_summary'):
                validated_data['data_summary'] = {}
            validated_data['data_summary']['events'] = data['events']

        activity = Activity.objects.create(**validated_data)

        # overwrite the created time with a client-provided value
        if created_time:
            activity.created = created_time
            activity.save()

        # create the ActivityData model 
        data.update({"activity": activity.pk})
        data_serializer = ActivityDataSerializer(data=data)
        if data_serializer.is_valid():
            data_serializer.save()
        return activity

    def to_representation(self, instance):
        representation = super(ActivitySerializer, self).to_representation(instance)
        representation['created'] = int(instance.created.timestamp() * 1e3)
        representation['user_obj'] = UserSerializer(instance.user).data

        try:
            representation['type_definition'] = instance.type_definition.type_obj
            representation['type_hash'] = instance.type_definition.pk
        except Exception as e:
            pass
        
        return representation  


class ActivityFavSerializer(BaseModelSerializer):
    activity = serializers.PrimaryKeyRelatedField(queryset=Activity.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=get_user_model().objects.all(), required=False)

    class Meta:
        model = ActivityFav
        fields = (
            'id',
            'activity',
            'user',
            'note'
        )

    def to_representation(self, instance):
        representation = super(ActivityFavSerializer, self).to_representation(instance)
        return representation


class ActivityAnnotationSerializer(BaseModelSerializer):
    activity = serializers.PrimaryKeyRelatedField(queryset=Activity.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=get_user_model().objects.all(), required=False)

    class Meta:
        model = ActivityAnnotation
        fields = (
            'id',
            'activity',
            'user',
            'body',
            'admin',
            'created',
            'modified'
        )

    def to_representation(self, instance):
        representation = super(ActivityAnnotationSerializer, self).to_representation(instance)
        representation['user'] = UserMiniSerializer(instance.user).data
        representation['created'] = int(instance.created.timestamp() * 1e3)
        representation['modified'] = int(instance.modified.timestamp() * 1e3)
        return representation


class LeaderboardItemSerializer(BaseModelSerializer):
    class Meta:
        model = Activity
        fields = (
            'id',
            'session',
            'user',
            'type_definition',
            'labels',
            'data_summary',
            'created'
        )

    def to_representation(self, instance):
        representation = super(LeaderboardItemSerializer, self).to_representation(instance)
        representation['created'] = int(instance.created.timestamp() * 1e3)

        representation['type_definition'] = instance.type_definition.type_obj
        representation['type_hash'] = instance.type_definition.pk        
        representation['user'] = UserSerializer(instance.user).data

        return representation  