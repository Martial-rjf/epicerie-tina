
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-pwz)i2t$o$g(stsz_jriwv8m8$yilztmwd4&)_x0ygf36+=z#a'

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
    'stocks',  # ✅ ton application
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',   # <-- Session d'abord
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # <-- Authentification (ajoute 'user')
    # ⬇️ Ton middleware personnalisé doit être APRÈS AuthenticationMiddleware
    #'stocks.middleware.ForceLogoutMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
  
]
# Expiration de la session à la fermeture du navigateur
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],  # Tu peux ajouter BASE_DIR / 'templates' si besoin
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
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
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Indian/Antananarivo'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Dans le confi/ settings.py 

#Configruration email (avec Gmail)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com' 
EMAIL_PORT= '587'
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'randriamihajajeanfelicem@gmail.com'
EMAIL_HOST_PASSWORD = 'Martial12f.a' 

# URLs Redirections pour l'authentification
LOGIN_REDIRECT_URL = '/accueil/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = '/login/'         # Après déconnexion → page login