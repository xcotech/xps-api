import datetime
import json
from rest_framework import viewsets, mixins, permissions
from django.conf import settings
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from xps_cloud.permissions import *
from xps_cloud.views import BaseViewSet, BaseModelViewSet
from xps_cloud.utils import api_serialize
from django.db.models import Q
from operator import itemgetter
from xps_cloud.redis import RedisObject

from .models import *
from .serializers import *

class SessionViewSet(BaseModelViewSet):
    queryset = Session.objects.all()
    serializer_class = SessionSerializer
    permission_classes = (permissions.IsAuthenticated, CanAdminOrReadOnly)
    filter_fields = ('org', 'name')
    cache_params = ['team', 'org']

    def get_queryset(self):
        queryset = super(SessionViewSet, self).get_queryset()
        if self.request.user.is_staff:
            # only staff are able to interact with sessions from any org
            org = self.request.query_params.get('org', None)
            if org:
                return queryset.filter(org__pk=org)
            return queryset.all()        

        # not staff, get user's primary org
        primary_org = org=self.request.user.orgs.order_by('pk').first().org
        return queryset.filter(org=primary_org)

    def create(self, request, *args, **kwargs):
        primary_org = org=self.request.user.orgs.order_by('pk').first().org
        if primary_org:
            request.data['org'] = primary_org.pk

        created = request.data.get('created', None)
        if created:
            request.data['created'] = datetime.datetime.fromtimestamp(created / 1e3)
                        
        return super(SessionViewSet, self).create(request, *args, **kwargs)

class ActivityViewSet(BaseModelViewSet):
    # queryset = Activity.objects.exclude(labels__contains=['incomplete'])
    queryset = Activity.objects.all()
    model = Activity
    serializer_class = ActivitySerializer
    permission_classes = (permissions.IsAuthenticated, OrgBasePermissions)
    filter_fields = ('session', 'user', 'type_definition')
    cache_key = 'a'
    cache_params = ['org','favs', 'session','user','activity_type','type_definition','type','distance','units','start_type','orientation','sort']

    def normalize_cache_params(self):
        # normalize query parameters so that we can generate a consistent, nuanced cache key
        query_params = {}

        # limit search to user's favorited activies?
        fetch_favs = True if 'favs' in self.request.query_params else False
        if fetch_favs:
            query_params['favs'] = True

        # only staff are allowed to see all orgs
        if self.request.user.is_staff:
            org = self.request.query_params.get('org', None)
            if org:
                query_params['org'] = org
        else:
            # primary user org
            org_member = self.request.user.orgs.order_by('pk').first()
            if org_member:
                query_params['org'] = org_member.org.pk

        # convenience aliases for query parameters
        param_aliases = {
            "type": "type_definition"
        }

        for option in self.cache_params:
            param = self.request.query_params.get(option, None)
            if param:
                if option == 'activity_type' and param == 'all':
                    continue
                if not getattr(query_params, option, None):                    
                    option = param_aliases.get(option, option)
                    query_params[option] = param

        return query_params

    def rebuild_cached_list(self):
        from apps.tracking.utils import get_target_time, get_target_velocity, get_user_activity_favs
        redis = RedisObject().get_redis_connection(slave=False)
        pipe = redis.pipeline()

        query_params = self.request.query_params.dict()
        base_queryset = self.get_queryset()
        query_filter = Q()       
        filters = []

        if 'favs' in query_params:
            fav_activity_tuples = get_user_activity_favs(self.request.user)
            favs = [i[1] for i in fav_activity_tuples] # get a flat list of activity pks
            filters.append(Q(pk__in=favs))

        for param in ['session', 'user', 'type_definition']:
            # check the param exists, and has a value
            if param in query_params and query_params[param]:
                filters.append(Q(**{'%s__id' % param: query_params[param]}))

        if 'activity_type' in query_params:
            activity_type = query_params['activity_type']
            filters.append(Q(type_definition__type_obj__activity_type=activity_type))

            if activity_type == 'jump':
                if 'orientation' in query_params:
                    filters.append(Q(type_definition__type_obj__orientation=query_params['orientation']))

        units = query_params.get('units', 'meters')
        distance = float(query_params.get('distance', 0))
        meters_per_yard = 0.9144            
        metric_distance = distance if units == "meters" else distance*meters_per_yard

        if distance:
            if units == 'yards':    
                filters.append(Q(Q(Q(type_definition__type_obj__units='yards') & Q(type_definition__type_obj__distance__gte=distance)) | Q(Q(Q(type_definition__type_obj__units__isnull=True) | Q(type_definition__type_obj__units='meters')) & Q(type_definition__type_obj__distance__gte=metric_distance))))
            else:
                filters.append(Q(Q(Q(type_definition__type_obj__units='yards') & Q(type_definition__type_obj__distance__gte=distance/meters_per_yard)) | Q(Q(Q(type_definition__type_obj__units__isnull=True) | Q(type_definition__type_obj__units='meters')) & Q(type_definition__type_obj__distance__gte=metric_distance))))

        if filters:
            for f in filters:
                query_filter &= f

        valid_sort_fields = ['time','vel','distance','height','created']
        sort_field = self.request.query_params.get('sort', None)
        sort_field = sort_field if sort_field in valid_sort_fields else None

        if not sort_field:
            # note: use created time as the score
            acts = base_queryset.filter(query_filter).values_list('pk','created')            
            scored_activities = [(a[0], int(a[1].timestamp())) for a in acts]
        else:
            # run the query, get some activities
            acts = base_queryset.filter(query_filter)  
            scored_activities = []
            # otherwise, we are confronting an invalid sort proposition
            for a in acts:
                score_value = None
                try:
                    if sort_field == 'height':
                        score_value = a.data_summary['height'] 
                    elif sort_field == 'distance':
                        score_value = a.data_summary['distance']                    
                    elif distance and sort_field == 'time':
                        score_value = get_target_time(a, metric_distance)
                    elif distance and sort_field == 'vel':
                        score_value = get_target_velocity(a, metric_distance)                     
                    elif sort_field == 'date':
                        score_value = int(a.created.timestamp())
                    else:
                        # invalid sort proposition:
                        score_value = int(a.created.timestamp())
                except Exception as e:
                    continue
                if score_value:                  
                    scored_activities.append((a.pk,score_value))

        if scored_activities:
            for at in scored_activities:
                redis.pipeline(self.list_cache.add_to_set(at[0],at[1]))
            pipe.expire(self.list_cache.key, settings.DEFAULT_CACHE_TIMEOUT)
            # pipe.expire(self.cache_set.key, 3) # testing
            pipe.execute()


    def get_queryset(self):
        queryset = self.queryset

        if self.request.user.is_staff:
            # only staff are able to get activities from other orgs
            org = self.request.query_params.get('org', None)
            if org:
                queryset = queryset.filter(session__org__pk=org)

        else:
            primary_org = self.request.user.get_primary_org()
            if primary_org:
                queryset = Activity.objects.filter(session__org=primary_org)
        
        type_hash = self.request.query_params.get('type', None)
        if type_hash:
            try:
                return queryset.filter(type_definition__pk=type_hash)
            except Exception as e:
                return queryset.none()
        return queryset

    def create(self, request, *args, **kwargs):
        created = request.data.get('created', None)
        if created:
            request.data['created'] = datetime.datetime.fromtimestamp(created / 1e3)

        session = request.data.get('session', None)
        type_definition = request.data.get('type_definition', None)
        request.data['data_summary'] = request.data.get('data_summary', None) or {}

        # catch new-session dicts passed from client; get a new model and move on
        if isinstance(session, dict):
            try:
                if 'id' in session:
                    request.data['session'] = int(session['id'])
                else:
                    session_model, created = Session.objects.get_or_create(**session)
                    request.data['session'] = session_model.pk
            except Exception as e:
                pass

        if type_definition and isinstance(type_definition, dict):
            activity_description_serializer = ActivityTypeSerializer(data={"type_obj": type_definition})

            # normalize the type_definition object
            if activity_description_serializer.is_valid(raise_exception=True):
                activity_description_serializer.save()    
                request.data['type_definition'] = activity_description_serializer.data['id']

        return super(ActivityViewSet, self).create(request, *args, **kwargs)

    def get_overlay_options(self, pks, scores=[]):
        from django.db.models.query import QuerySet
        from apps.tracking.utils import get_user_activity_favs

        # we always want lists here
        pks = pks if isinstance(pks, (list, QuerySet)) else [pks]
        if scores:
            scores = scores if isinstance(scores, (list, QuerySet)) else [scores]

        # get user's cached favourites list, indicate status on serialized object
        favs = get_user_activity_favs(self.request.user)
        
        # match an activity pk to a favourite object
        def get_fav(pk):
            matched_fav = [favs[i][0] for i, v in (enumerate(favs)) if v[1] == pk]
            return matched_fav[0] if len(matched_fav) else None

        if not scores:
            return [{'fav': get_fav(pk)} for pk in pks]
        return [{'score': scores[i], 'fav': get_fav(pk)} for i, pk in enumerate(pks)]


class ActivityDataViewSet(viewsets.ModelViewSet):
    queryset = ActivityData.objects.all()
    serializer_class = ActivityDataSerializer
    permission_classes = (permissions.IsAuthenticated, CanAdminOrReadOnly)
    # filter_fields = ('activity', )

    def get_queryset(self):
        # get activity.pk
        activity_pk = self.kwargs.get('pk', None)
        if activity_pk:
            # get activity_data matching this pk (OneToOne field)
            try:
                self.kwargs['pk'] = ActivityData.objects.get(activity__id=activity_pk).pk
                all_data = self.request.query_params.get('all', None)
                if all_data:
                    return ActivityData.objects.filter(id=self.kwargs['pk'])
                return ActivityData.objects.only('est', 'events', 'activity').filter(id=self.kwargs['pk']) # omit potentially expensive raw/eng data
            except Exception as e:
                print('failed to assign new pk to activity_data kwargs: %s' % e)

        # org_pks = self.request.user.orgs.values_list('org', flat=True)
        return ActivityData.objects.none()


class ActivityTypeViewSet(BaseModelViewSet):
    queryset = ActivityType.objects.all()
    serializer_class = ActivityTypeSerializer
    permission_classes = (permissions.IsAuthenticated, CanAdminOrReadOnly)

class ActivityFavViewSet(BaseModelViewSet):
    queryset = ActivityFav.objects.all()
    serializer_class = ActivityFavSerializer
    permission_classes = (permissions.IsAuthenticated, CanAdmin)
    filter_fields = ('activity', 'user',)
    cache_params = ['team', 'org']

    def create(self, request, *args, **kwargs):
        request.data['user'] = self.request.user.pk                        
        return super(ActivityFavViewSet, self).create(request, *args, **kwargs)

class ActivityAnnotationViewSet(BaseModelViewSet):
    queryset = ActivityAnnotation.objects.all()
    serializer_class = ActivityAnnotationSerializer
    permission_classes = (permissions.IsAuthenticated, CanAdmin)
    filter_fields = ('activity', 'user', 'admin')
    cache_params = ['activity', 'admin', 'user']

    def create(self, request, *args, **kwargs):
        request.data['user'] = self.request.user.pk                        
        return super(ActivityAnnotationViewSet, self).create(request, *args, **kwargs)
