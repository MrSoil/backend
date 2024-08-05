"""
Django settings for backend project.

Generated by 'django-admin startproject' using Django 3.2.25.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

from pathlib import Path
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-j%c=1xnn&0cx39ds9=$0kfhd)-4h(krb*4&dq5^!@lvnx5$2#r'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'sugr_backend',
    'corsheaders',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',

]

ROOT_URLCONF = 'backend.urls'

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

WSGI_APPLICATION = 'backend.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
      'default': {
          'ENGINE': 'djongo',
          'NAME': 'sugrBE',
          'CLIENT': {
              'host': 'localhost',
              'port': 27017,
              'username': 'admin',
              'password': 'admin'
          }
      }
   }


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    )
}

AUTH_USER_MODEL = 'sugr_backend.User'

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),     # Token is valid for 5 minutes
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),    # You can request a new access token using the refresh token within this time
    'ROTATE_REFRESH_TOKENS': False,                 # Whether to issue a new refresh token on token refresh
    'BLACKLIST_AFTER_ROTATION': True,               # Whether to blacklist the old tokens after rotation

    'ALGORITHM': 'HS256',                           # The signing algorithm to use when encoding tokens
    'SIGNING_KEY': SECRET_KEY,          # Signing key to encode and decode JWT tokens
    'VERIFYING_KEY': None,                          # The verifying key. It’s None unless asymmetric algos like RSA are used

    'AUTH_HEADER_TYPES': ('Bearer',),               # The type of header expected ('Bearer' tokens)
    'USER_ID_FIELD': 'id',                          # The field in the User model that is used as the user identifier
    'USER_ID_CLAIM': 'user_id',                     # The claim name for the user identifier

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),  # Type of tokens issued
    'TOKEN_TYPE_CLAIM': 'token_type',               # Field name for token type in payload

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',  # Field name in sliding tokens for refresh expiration
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),    # Lifetime of sliding tokens
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),  # Refresh lifetime of sliding tokens
}

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
]

CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
