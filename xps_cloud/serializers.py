import time, datetime, json

from rest_framework import serializers

class JSONSerializerField(serializers.Field):
    """ Serializer for JSONField -- required to make field writable"""
    def to_internal_value(self, data):
        return data
    def to_representation(self, value):
        return value

class BaseModelSerializer(serializers.ModelSerializer): 
    cache_class = "base"
    do_cache = True
    
    def check_synced(self, validated_data):
        ''' lookup for previously synced models, given a sync_id from the client '''        
        sync_id = validated_data.get('sync_id', None)
        if sync_id:
            try:
                return self.Meta.model.objects.get(sync_id=sync_id) 
            except Exception as e:
                pass
        return None


