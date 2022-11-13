from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.reverse import reverse
import base64
import json
import os
from xps_cloud.permissions import CanAdminOrReadOnly, OrgBasePermissions, CanAdmin
from xps_cloud.views import BaseModelViewSet
from xps_cloud.utils import api_serialize
from apps.org.models import *
from apps.org.serializers import *

class OrgViewSet(BaseModelViewSet):
    queryset = Org.objects.all()
    serializer_class = OrgSerializer
    permission_classes = (permissions.IsAuthenticated, CanAdmin)

    def get_queryset(self):
        queryset = super(OrgViewSet, self).get_queryset()

        if self.request.user.is_staff:
            # only staff are allowed to switch between orgs
            org = self.request.query_params.get('org', None)
            if org:
                return queryset.filter(pk=org)
            return queryset.all()  
        return queryset.filter(pk=self.request.user.orgs.order_by('pk').first().org.pk)


class OrgSystemViewSet(BaseModelViewSet):
    queryset = OrgSystem.objects.all()
    serializer_class = OrgSystemSerializer
    permission_classes = (permissions.IsAuthenticated, CanAdminOrReadOnly)
    filter_fields = ('org', 'system')
    cache_params = ['system']

    def get_queryset(self):
        queryset = super(OrgSystemViewSet, self).get_queryset()
        if self.request.user.is_staff:
            org = self.request.query_params.get('org', None)
            if org:
                return queryset.filter(org__pk=org)
            return queryset.all()        
        return queryset.filter(org=self.request.user.orgs.order_by('pk').first().org)

class OrgTagViewSet(BaseModelViewSet):
    queryset = OrgTag.objects.all()
    serializer_class = OrgTagSerializer
    permission_classes = (permissions.IsAuthenticated, CanAdmin)
    filter_fields = ('org', 'tag')

    def get_queryset(self):
        queryset = super(OrgTagViewSet, self).get_queryset()
        if self.request.user.is_staff:
            org = self.request.query_params.get('org', None)
            if org:
                return queryset.filter(org__pk=org)
            return queryset.all()        
        return queryset.filter(org=self.request.user.orgs.order_by('pk').first().org)
    

class OrgMemberViewSet(BaseModelViewSet):
    queryset = OrgMember.objects.all()
    model = OrgMember
    serializer_class = OrgMemberSerializer
    permission_classes = (permissions.IsAuthenticated, CanAdminOrReadOnly)
    filter_fields = ('org', 'user')
    cache_params = ['org', 'user']

    def rebuild_list_cache(self):
        from xps_cloud.redis import RedisObject
        from apps.org.utils import get_summary_stats
        from django.db.models import Q
        redis = RedisObject().get_redis_connection(slave=False)
        pipe = redis.pipeline()

        query_filter = Q()       

        filters = []
        if self.org_pk:
            filters.append(Q(org__id=self.org_pk))

        if filters:
            for f in filters:
                query_filter &= f

        valid_sort_fields = ['distance','height','max_velocity','num_activities']
        sort_field = self.request.query_params.get('sort', None)
        sort_field = sort_field if sort_field in valid_sort_fields else None

        if not sort_field:
            # note: use created time as the score
            objs = self.get_queryset().filter(query_filter).values_list('pk','created')
            scored_objs = [(o[0], int(o[1].timestamp())) for o in objs]            
        else:
            scored_objs = []
            objs = self.get_queryset().filter(query_filter)
            for o in objs:
                summary_stats = o.get_summary_stats()
                if summary_stats:
                    scored_objs.append((o.pk, summary_stats.get(sort_field, 0)))

        if scored_objs:
            for so in scored_objs:
                redis.pipeline(self.cache_set.add_to_set(so[0],so[1]))
            pipe.expire(self.cache_set.key, settings.DEFAULT_CACHE_TIMEOUT)
            # pipe.expire(self.cache_set.key, 3) # testing
            pipe.execute()

    def get_queryset(self):
        queryset = super(OrgMemberViewSet, self).get_queryset()
        if self.request.user.is_staff:
            # only staff are able to see all OrgMember objects
            org = self.request.query_params.get('org', None)
            if org:
                if org == "all":
                    return queryset
                return queryset.filter(org__pk=org)
            return queryset.all()

        team_pk = self.request.GET.get('team')
        primary_org = self.request.user.orgs.order_by('pk').first().org

        if team_pk:
            try:
                team = get_team_model().objects.get(pk=team_pk)
            except:
                return OrgMember.objects.none()
            team_pks = OrgMember.objects.values_list('teams', flat=True)
            return OrgMember.objects.filter(pk__in=list(team_pks)).filter(org=primary_org)

        return OrgMember.objects.filter(org=primary_org)

    def create(self, request, *args, **kwargs):
        user_model = None
        user = request.data.get('user', None)
        org = request.data.get('org', None)

        # remove invalid teams, just in case
        teams = request.data.pop('teams', None)
        if teams:
            request.data['teams'] = Team.objects.filter(org=org, pk__in=list(teams)).values_list('pk', flat=True)

        if type(user) is dict:

            if 'username' in user:
                try:
                    user_model = get_user_model().objects.get(username=user['username'])
                except Exception as e:
                    print(e)
                    pass
            user_model = get_user_model().objects.add_user(**user)

        if user_model:
            request.data['user'] = user_model.pk

        return super(OrgMemberViewSet, self).create(request, *args, **kwargs)


class TeamViewSet(BaseModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = (permissions.IsAuthenticated, CanAdminOrReadOnly)
    filter_fields = ('org', )

    def get_queryset(self):
        queryset = super(TeamViewSet, self).get_queryset()

        if self.request.user.is_staff:
            # only staff are able to interact with teams from any org
            org = self.request.query_params.get('org', None)
            if org:
                return queryset.filter(org__pk=org)
            return queryset.all()        

        # not staff, get user's primary org
        primary_org = org=self.request.user.orgs.order_by('pk').first().org
        return queryset.filter(org=primary_org)


class OrgFeatureViewSet(BaseModelViewSet):
    queryset = OrgFeature.objects.all()
    serializer_class = OrgFeatureSerializer
    permission_classes = (permissions.IsAuthenticated, CanAdminOrReadOnly)
    filter_fields = ('org', 'feature')
    cache_params = ['org', 'feature']

class AdminFeatureViewSet(BaseModelViewSet):
    queryset = Feature.objects.all()
    serializer_class = FeatureSerializer
    permission_classes = (permissions.IsAuthenticated, CanAdminOrReadOnly)
