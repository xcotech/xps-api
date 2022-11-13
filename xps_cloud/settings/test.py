from xps_cloud.settings.base import *

DEBUG = True

DATABASES = {
    'default': env.db(default='postgres://postgres:postgres@db/test_xps_test'),
    'slave1': env.db(default='postgres://postgres:postgres@db/test_xps_test'), 
    'slave2': env.db(default='postgres://postgres:postgres@db/test_xps_test')
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
    'sessions': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)
