import json

from django.http import HttpResponse
from django.views.generic import CreateView
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from rest_framework import viewsets, permissions, mixins
from xps_cloud.views import BaseViewSet, BaseModelViewSet
from xps_cloud.permissions import CanAdminOrReadOnly
from xps_cloud.utils import create_jwt

from .serializers import *
from .forms import *

class UserViewSet(BaseModelViewSet):
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated, CanAdminOrReadOnly)

    def create(self, request, *args, **kwargs):
        # admins can provide a password, or use default
        password = request.data.get('password', 'xps')
        return super(UserViewSet, self).create(request, *args, **kwargs)

    def get_queryset(self):
        return get_user_model().objects.all()


class UserImageViewSet(viewsets.ModelViewSet):
    queryset = UserImage.objects.all()
    serializer_class = UserImageSerializer
    permission_classes = (permissions.IsAuthenticated, CanAdminOrReadOnly)

    def perform_create(self, serializer):
        user = get_user_model().objects.get(pk=self.request.data.get('user'))
        public_id = self.request.data.get('public_id')
        primary = self.request.data.get('primary')
        serializer.save(user=user,public_id=public_id,primary=primary)
