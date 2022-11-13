import os, logging, json

import urllib3
from urllib.parse import urlencode, quote_plus

from django.conf import settings
import base64
from django.http import HttpResponse, Http404
from django.contrib.contenttypes.models import ContentType
from xps_cloud.mixins import MultiSerializerViewSetMixin
from xps_cloud.cache import ModelSortedSet
from rest_framework import filters, viewsets
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from django.views.generic.base import View
from rest_framework.reverse import reverse
from django.shortcuts import get_object_or_404

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from xps_cloud.utils import api_serialize

def app_status(request):
    ''' can we at least do this? '''
    return HttpResponse('ok')

class BaseViewSet(viewsets.ViewSet):
    permission_classes = (AllowAny, )
    
    def render_to_json_response(self, context, **response_kwargs):
        data = json.dumps(context)
        response_kwargs['content_type'] = 'application/json'
        return HttpResponse(data, **response_kwargs)

class BaseModelViewSet(MultiSerializerViewSetMixin, viewsets.ModelViewSet):
    fetch_related = None
    model = None
    cache_key = None
    list_cache_class = ModelSortedSet
    filter_backends = (filters.SearchFilter, DjangoFilterBackend,)
    search_fields = ()
    filter_fields = ()
    permission_classes = (AllowAny, )
    sort_fields = []
    cache_params = []

    serializer_action_classes = {}    

    def retrieve(self, request, pk=None):
        # stop here if 1) no object; or 2) user does not have object permissions
        obj = get_object_or_404(self.queryset, **{"pk":pk})
        self.check_object_permissions(request, obj)
        return Response(api_serialize(self.serializer_class, pk, self.get_overlay_options(pk)))

    def rebuild_cached_list(self):
        from xps_cloud.redis import RedisObject
        redis = RedisObject().get_redis_connection(slave=False)
        pipe = redis.pipeline()
        scored_objs = self.get_queryset().values_list('pk', 'created')
        if scored_objs:
            # format default score (created datetime object) as int(timestamp())
            scored_objs = [(s[0], int(s[1].timestamp())) for s in scored_objs]            
            for so in scored_objs:
                redis.pipeline(self.list_cache.add_to_set(so[0],so[1]))
            pipe.expire(self.list_cache.key, settings.DEFAULT_CACHE_TIMEOUT)
            pipe.execute()

    def normalize_cache_params(self):
        # normalize query parameters
        query_params = {}
        # only staff are allowed to switch between orgs
        if self.request.user.is_staff:
            org = self.request.query_params.get('org', None)
            if org:
                query_params['org'] = org
        else:
            # primary user org
            org_member = self.request.user.orgs.order_by('pk').first()
            if org_member:
                query_params['org'] = org_member.org.pk
        
        for option in self.cache_params:
            param = self.request.query_params.get(option, None)
            if param:
                if not getattr(query_params, option, None):
                    query_params[option] = param
        return query_params

    def get_encoded_cache_params(self):
        return base64.urlsafe_b64encode(json.dumps(self.normalize_cache_params()).encode()).decode()

    def list(self, request, *args, **kwargs):
        from django.urls import resolve
        
        start_param = self.request.query_params.get('start', 0)
        end_param = self.request.query_params.get('end', 0)
        page_num = None

        cursor_start = int(start_param)
        if not start_param:
            page_num = int(self.request.query_params.get('page', 1))
            cursor_start = int((page_num-1) * settings.DEFAULT_PAGE_SIZE)
        cursor_end = int(self.request.query_params.get('end', cursor_start + settings.DEFAULT_PAGE_SIZE - 1))

        # we might want this in reverse order
        self.order_asc = self.request.query_params.get('order', 'desc') == 'asc'

        content_type = ContentType.objects.get_for_model(self.queryset.model).pk
        encoded_params = self.get_encoded_cache_params()
        # use encoded params to get the list cache object
        self.list_cache = self.list_cache_class(content_type, encoded_params)        
       
        # note: we always fetch lists of sorted pks, 
        # and propagate the score value into the serialized object with self.get_overlay_options
        # start, end, ascending (boo)
        scored_pks = self.list_cache.get_set_with_scores(cursor_start, cursor_end, self.order_asc)
        if not scored_pks:
            self.rebuild_cached_list()
            scored_pks = self.list_cache.get_set_with_scores(cursor_start, cursor_end)
        scored_pks = [(int(i[0]), i[1]) for i in scored_pks]

        list_count = self.list_cache.get_set_count()

        # for backward compatibility, where needed (if we have not explicitly used next/previous) build up next/previous urls 
        next_url = None
        previous_url = None
        if page_num: # otherwise, we are explicitly using start/end cursor pagination
            try:
                params_dict = self.request.query_params.dict()
                if hasattr(params_dict, 'page'):
                    del params_dict['page']

                api_root = reverse(resolve(request.path_info).url_name, request=request)                
                if page_num > 1:
                    previous_url = os.path.join(api_root, '?%s' % urlencode(dict(params_dict, **{"page": page_num-1})))
                if list_count - 1  > page_num * settings.DEFAULT_PAGE_SIZE:                    
                    next_url = os.path.join(api_root, '?%s' % urlencode(dict(params_dict, **{"page": page_num+1})))
            except Exception as e:
                print(e)

        return Response({
                'count': list_count,
                'start': cursor_start,
                'end': cursor_start + len(scored_pks),
                'next': next_url,
                'previous': previous_url,
                'results': api_serialize(self.serializer_class, [p[0] for p in scored_pks], self.get_overlay_options([p[0] for p in scored_pks], [p[1] for p in scored_pks]))
            })

    def get_overlay_options(self, pks, scores=None):
        # no options by default
        return []
        
    def setup_eager_loading(self, queryset):
        return queryset.prefetch_related(self.fetch_related)

    def get_queryset(self): 
        # Set up eager loading to avoid N+1 selects
        queryset = self.setup_eager_loading(self.queryset)
        filter_kwargs = {}

        for param in self.filter_fields:
            param_val = self.request.query_params.get(param, None)
            if param_val and param_val is not None:
                filter_kwargs['%s' % param] = param_val

        if filter_kwargs:
            queryset = queryset.filter(**filter_kwargs)

        return queryset