from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static

from rest_framework import routers
from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token, verify_jwt_token

from xps_cloud import views as xps_cloud_views
from apps.user import views as user_api
from apps.tracking import views as tracking_api
from apps.system import views as system_api
from apps.org import views as org_api
from apps.admin import views as admin_api


# define our API router
router = routers.DefaultRouter(trailing_slash=True)

# user api
router.register('user', user_api.UserViewSet, basename='user')
router.register('user_image', user_api.UserImageViewSet, basename='user_image')

# system_api api
router.register('system', system_api.SystemViewSet, basename='system')
router.register('tag', system_api.TagViewSet, basename='tag')
router.register('tag_build', system_api.TagBuildViewSet, basename='tag_build')
router.register('system_build', system_api.SystemBuildViewSet, basename='system_build')
router.register('hub_firmware', system_api.HubFirmwareViewSet, basename='hub_firmware')
router.register('logger', system_api.SystemEventLogEntryViewSet, basename='logger')

# org api
router.register('org', org_api.OrgViewSet, basename='org')
router.register('org_system', org_api.OrgSystemViewSet, basename='org_system')
router.register('org_tag', org_api.OrgTagViewSet, basename='org_tag')
router.register('org_member', org_api.OrgMemberViewSet, basename='org_member')
router.register('org_feature', org_api.OrgFeatureViewSet, basename='org_feature')
router.register('team', org_api.TeamViewSet, basename='team')
router.register('feature', org_api.AdminFeatureViewSet, basename='feature')

# stats api
router.register('stats', admin_api.StatsViewSet, basename='stats')

# tracking api
router.register('session', tracking_api.SessionViewSet, basename='session')
router.register('activity', tracking_api.ActivityViewSet, basename='activity')
router.register('activity_type', tracking_api.ActivityTypeViewSet, basename='activity_type')
router.register('activity_data', tracking_api.ActivityDataViewSet, basename='activity_data')
router.register('activity_fav', tracking_api.ActivityFavViewSet, basename='activity_fav')
router.register('activity_annotation', tracking_api.ActivityAnnotationViewSet, basename='activity_annotation')


urlpatterns = [
    path('app_status', xps_cloud_views.app_status, name='app_status'),
]

# api level paths
urlpatterns += [
    path('api/login/', obtain_jwt_token, name='login'),
    path('api/token/refresh/', refresh_jwt_token, name='refresh_token'),
    path('api/token/verify/', verify_jwt_token, name='verify_token'),
    path('api/', include(router.urls)),
]
