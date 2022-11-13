from xps_cloud.settings.base import *

DATABASES = {
    'default': env.db(default='postgres://postgres:postgres@127.0.0.1:5432/xps_cloud_test')
}
