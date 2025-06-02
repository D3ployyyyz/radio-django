import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# SECRET_KEY e DEBUG via variáveis de ambiente, com fallback para desenvolvimento local
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-21oy1224h1#v=8668h97t#5$zmhc5$zmhc5gxcand@l0yhb!8c##=6t7')
DEBUG = os.getenv('DEBUG', 'True') == 'True'

# Hosts permitidos - padrão localhost e Railway, mas pode ser configurado pela env var
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,0.0.0.0').split(',')

INSTALLED_APPS = [
    'radio',  # Seu app principal
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # Whitenoise para servir arquivos estáticos em produção, recomendado no Railway
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'radio_django.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],  # Templates dentro dos apps
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

WSGI_APPLICATION = 'radio_django.wsgi.application'

# Banco de dados configurado via DATABASE_URL, com fallback para SQLite local
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        # ssl_require removido para evitar problemas
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'

USE_I18N = True
USE_L10N = True
USE_TZ = True

# Diretórios para arquivos estáticos durante o desenvolvimento
STATICFILES_DIRS = [
    BASE_DIR / 'radio' / 'static',
]

# URL para acessar arquivos estáticos (via navegador)
STATIC_URL = '/static/'

# Diretório onde collectstatic irá colocar arquivos para produção
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Whitenoise configurações para cache de arquivos estáticos (produção)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
