import sys
import environ

root = environ.Path(__file__) - 2 # three folder back (/a/b/c/ - 3 = /)
env = environ.Env(DEBUG=(bool, False),) # set default values and casting
environ.Env.read_env() # reading .env file

SITE_ROOT = root()


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', default='MY-SECRET') # Raises ImproperlyConfigu   exception if SECRET_KEY not in os.environ

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG') # False if not in os.environ

hosts = env('ALLOWED_HOSTS', default=['localhost', '192.168.1.71', '192.168.1.71:8000'])
# ALLOWED_HOSTS = [x for x in hosts.split(',')]
ALLOWED_HOSTS = ['xps.xco.io', 'localhost', '192.168.1.71', '192.168.1.71:8000']

AUTH_USER_MODEL = 'user.User'
SITE_URL = env('SITE_URL', default='localhost')

# DATA_UPLOAD_MAX_MEMORY_SIZE = 2621440
DATA_UPLOAD_MAX_MEMORY_SIZE = 262144000

DEFAULT_PAGE_SIZE = 20
DEFAULT_CACHE_TIMEOUT = 86400

# Application definition
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',

    'rest_framework',
    'django_filters',

    'apps.user',
    'apps.system',
    'apps.org',
    'apps.tracking',
    'apps.admin'
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'multidb.middleware.PinningRouterMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

###########################################################
# CORS settings
###########################################################
CORS_ORIGIN_ALLOW_ALL = True
CORS_ORIGIN_WHITELIST = (
    'https://xps.xco.io',
    'http://localhost:8000',
    'http://xco:8000'
)

CSRF_TRUSTED_ORIGINS = (
    '*',
)

ROOT_URLCONF = 'xps_cloud.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'xps_cloud.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': env.db(default='postgres://postgres:postgres@db/xps'), # Raises ImproperlyConfigured exception if DATABASE_URL not in os.environ
    'slave1': env.db('SLAVE1_URL', default='postgres://postgres:postgres@db/xps'), 
    'slave2': env.db('SLAVE2_URL', default='postgres://postgres:postgres@db/xps'), 
}

DATABASE_ROUTERS = ('multidb.PinningReplicaRouter',)
REPLICA_DATABASES = ['slave1']

MULTIDB_PINNING_SECONDS = 5 # seconds to pin a write database connection
MULTIDB_PINNING_COOKIE = 'db_pin_writes'

REDIS_SLAVE_HOST = env('REDIS_SLAVE_HOST', default='redis_db')
REDIS_MASTER_HOST = env('REDIS_MASTER_HOST', default='redis_db')

# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_URL = '/static/'

# Storages
DEFAULT_FILE_STORAGE = env('DEFAULT_FILE_STORAGE', default='storages.backends.s3boto3.S3Boto3Storage')

AWS_IS_GZIPPED=True
AWS_S3_CUSTOM_DOMAIN='dj0s6lxhdlnt1.cloudfront.net'
AWS_STORAGE_BUCKET_NAME='xps-static-files'

CLOUDINARY_CLOUD_NAME = env('CLOUDINARY_CLOUD_NAME', default='xps')
CLOUDINARY_API_KEY = env('CLOUDINARY_API_KEY', default='key')
CLOUDINARY_API_SECRET = env('CLOUDINARY_API_SECRET', default='secret')

S3_IMAGE_URL = env('S3_IMAGE_URL', default='https://d24n2tvjr0rgjx.cloudfront.net')
S3_IMAGE_SMALL = env('S3_IMAGE_SMALL', default='small')
S3_IMAGE_LARGE = env('S3_IMAGE_LARGE', default='large')
S3_IMAGE_FULL = env('S3_IMAGE_FULL', default='original')

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,  # TODO - lower this very soon.
    'TEST_REQUEST_DEFAULT_FORMAT': 'json'
}

# setup the default payload handler to return a user with the token.
JWT_AUTH = {
    'JWT_RESPONSE_PAYLOAD_HANDLER': 'xps_cloud.utils.jwt_response_payload_handler',
    'JWT_VERIFY_EXPIRATION': False,  # TODO - set this to a reasonable time after initial dev.
}

