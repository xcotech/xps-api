import datetime
from rest_framework import viewsets, permissions
from rest_framework.parsers import FormParser, MultiPartParser

from xps_cloud.permissions import CanAdminOrReadOnly
from xps_cloud.views import BaseModelViewSet

from apps.system.models import *
from apps.system.serializers import *
from apps.org.models import Org, OrgTag, OrgSystem

class SystemViewSet(BaseModelViewSet):
    queryset = System.objects.all()
    serializer_class = SystemSerializer
    permission_classes = (permissions.IsAuthenticated, CanAdminOrReadOnly)
    filter_fields = ('serial_num', 'build',)
    cache_params = ['build', 'org']

    def get_queryset(self):
        # queryset = self.queryset
        queryset = super(SystemViewSet, self).get_queryset()
        if self.request.user.is_staff:
            # only staff are able to get activities from other orgs
            org = self.request.query_params.get('org', None)
            if org:
                return queryset.filter(orgs__org=org)
            return queryset.all()

        primary_org = self.request.user.orgs.order_by('pk').first().org
        if primary_org:
            return queryset.filter(orgs__org=primary_org.pk)
        return queryset.none()

    def update(self, request, pk=None, *args, **kwargs):       
        manufacture_date = request.data.get('manufacture_date', None)
        if isinstance(manufacture_date, int):
            try:
                request.data['manufacture_date'] = datetime.datetime.fromtimestamp(manufacture_date)
            except Exception as e:
                print(e)
                pass
        return super(SystemViewSet, self).update(request, pk, *args, **kwargs)

    def create(self, request, *args, **kwargs): 
        try:  
            manufacture_date = request.data.get('manufacture_date', None)
            if manufacture_date:
                request.data['manufacture_date'] = datetime.datetime.fromtimestamp(manufacture_date)
            else:
                request.data['manufacture_date'] = datetime.datetime.now()                       
            return super(SystemViewSet, self).create(request, *args, **kwargs)
        except Exception as e:
            print(e)

class SystemBuildViewSet(BaseModelViewSet):
    queryset = SystemBuild.objects.all()
    serializer_class = SystemBuildSerializer
    permission_classes = (permissions.IsAuthenticated, CanAdminOrReadOnly, )
    filter_fields = ('system', )
    cache_params = ['system']

    def create(self, request, *args, **kwargs):  
        build_date = request.data.get('build_date', None)
        if build_date:
            request.data['build_date'] = datetime.datetime.fromtimestamp(build_date)
        else:
            request.data['build_date'] = datetime.datetime.now()                        
        return super(SystemBuildViewSet, self).create(request, *args, **kwargs)

class TagBuildViewSet(BaseModelViewSet):
    queryset = TagBuild.objects.all()
    serializer_class = TagBuildSerializer
    permission_classes = (permissions.IsAuthenticated, CanAdminOrReadOnly, )
    filter_fields = ('tag',)
    cache_params = ['tag']

    def create(self, request, *args, **kwargs):        
        build_date = request.data.get('build_date', None)
        if build_date:
            request.data['build_date'] = datetime.datetime.fromtimestamp(build_date)
        else:
            request.data['build_date'] = datetime.datetime.now()                    
        return super(TagBuildViewSet, self).create(request, *args, **kwargs)

class TagViewSet(BaseModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.IsAuthenticated, )
    filter_fields = ('serial_num','name')
    cache_params = ['build']

    def get_queryset(self):
        queryset = self.queryset
        if self.request.user.is_staff:
            # only staff are able to get activities from other orgs
            org = self.request.query_params.get('org', None)
            if org:
                return queryset.filter(orgs__org=org)
            return queryset.all()

        primary_org = self.request.user.orgs.order_by('pk').first().org
        if primary_org:
            return queryset.filter(orgs__org=primary_org.pk)
        return queryset.none()

    def create(self, request, *args, **kwargs):  
        manufacture_date = request.data.get('manufacture_date', None)
        if manufacture_date:
            request.data['manufacture_date'] = datetime.datetime.fromtimestamp(manufacture_date)
        else:
            request.data['manufacture_date'] = datetime.datetime.now()                       
        return super(TagViewSet, self).create(request, *args, **kwargs)

class SystemEventLogEntryViewSet(BaseModelViewSet):
    queryset = SystemEventLogEntry.objects.all()
    serializer_class = SystemLogSerializer
    permission_classes = (permissions.IsAuthenticated, )
    filter_fields = ('system',)

class HubFirmwareViewSet(BaseModelViewSet):
    queryset = HubFirmware.objects.all()
    permission_classes = (permissions.IsAuthenticated, CanAdminOrReadOnly,)
    serializer_class = HubFirmwareSerializer
    parser_classes = (MultiPartParser, FormParser,)

    def create(self, request, *args, **kwargs):                        
        return super(HubFirmwareViewSet, self).create(request, *args, **kwargs)
