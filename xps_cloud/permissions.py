from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie

from rest_framework import permissions, viewsets

class OrgBasePermissions(permissions.BasePermission):
    """
    Custom permissions for XPS model views
    """

    def has_permission(self, request, view):
        ''' list-level permissions '''
        if request.user.is_staff:
            return True
        try:
            org_member = request.user.get_org_member()
            if org_member.has_permission('OrgIsCoach'):
                print('has permission: OrgIsCoach')
            return True
        except Exception as e:
            print('OrgBasePermissions.has_permission error: %s' % e)
        return False

    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True
        # Write permissions are only allowed if they pass can_admin
        return obj.can_admin(request.user)


class CanAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission.
        Allow read for any
        Allow write if user passes can_admin test at model level
    """

    def has_permission(self, request, view):
        if request.user and request.user.is_staff:
            return True
        return True

    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True
        return obj.can_admin(request.user)

class CanAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        # move along to the has_object_permission() check
        return True

    ''' strict instance-based permissions '''
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True
        return obj.can_admin(request.user)