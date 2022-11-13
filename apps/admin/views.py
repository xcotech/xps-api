import datetime
import json
from rest_framework import viewsets, mixins, permissions
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from xps_cloud.permissions import CanAdminOrReadOnly, OrgBasePermissions
from xps_cloud.views import BaseViewSet, BaseModelViewSet
from django.db.models import Q
from operator import itemgetter
from xps_cloud.redis import RedisObject

from .serializers import *
from .stats import get_stats

class StatsViewSet(BaseViewSet):

    def list(self, request, *args, **kwargs):
        return Response(get_stats(request))        