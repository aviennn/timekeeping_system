"""
Django settings for timekeeps project.

Generated by 'django-admin startproject' using Django 5.1.5.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-vbs&$58+s$t!+mf_80w$@*(8eh&ao-ffh7%$z%om%kl=d(+10l'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'TimeKeeping_App',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'timekeeps.urls'

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

WSGI_APPLICATION = 'timekeeps.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'timekeeping_system', 
        'USER': 'root',  
        'PASSWORD': 'put database password here',  
        'HOST': 'localhost',  
        'PORT': '3306',  
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Manila'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

JAZZMIN_SETTINGS = {
    "site_title": "Academe TS",
    "site_header": "Academe TS",
    "site_brand": "Academe TS",
    "site_logo":"images/icon-1.png",
    "login_logo":"images/icon-1.png",
    "login_logo_dark":"images/icon-2.png",
    #"site_logo_classes": "",
    "site_icon":"images/favicon.png",
    "welcome_sign": "Academe TS by GOCLOUD",
    "copyright": "GOCLOUD Asia, Inc",
    #"search_model": ["auth.User", "auth.Group"],
    "user_avatar": "",

    # TOP MENU

    "topmenu_links": [
        #{"name": "Home",  "url": "admin:index", "permissions": ["auth.view_user"]},
        #{"name": "GOCLOUD Website", "url": "https://gocloudgroup.com/", "new_window": True},
        #{"model": "auth.User"},
        #{"app": "TimeKeeping_App"},
    ],

    # USER MENU

    "usermenu_links": [
        {"name": "GOCLOUD Website", "url": "https://gocloudgroup.com/", "new_window": True, "icon": "fas fa-globe"},
        #{"model": "auth.user"}
    ],

    # SIDE MENU

    #"show_sidebar": True,
    #"navigation_expanded": True,
    #"hide_apps": [],
    #"hide_models": [],
    #"order_with_respect_to": ["auth", "books", "books.author", "books.book"],

    #"custom_links": {
        #"books": [{
            #"name": "Make Messages", 
            #"url": "make_messages", 
            #"icon": "fas fa-comments",
            #"permissions": ["books.view_book"]
        #}]
    #},

    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "TimeKeeping_App.employee": "fas fa-user-tie",
        "TimeKeeping_App.timerecord": "far fa-clock	",
    },

    #"default_icon_parents": "fas fa-chevron-circle-right",
    #"default_icon_children": "fas fa-circle",

    # RELATED MODAL

    #"related_modal_active": False,

    # UI TWEAKS

    "custom_css": "css/jazzmin.css",
    #"custom_js": None,
    "use_google_fonts_cdn": True,
    "show_ui_builder": True,

    # CHANGE VIEW
    "changeform_format": "horizontal_tabs",
    #"changeform_format_overrides": {"auth.user": "collapsible", "auth.group": "vertical_tabs"},
    #"language_chooser": True,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-dark",
    "accent": "accent-info",
    "navbar": "navbar-primary navbar-dark",
    "no_navbar_border": True,
    "navbar_fixed": False,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": False,
    "sidebar": "sidebar-light-teal",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": True,
    "theme": "flatly",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-outline-primary",
        "secondary": "btn-outline-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'academetsmain@gmail.com'
EMAIL_HOST_PASSWORD = 'put password here' # MAKE SURE TO DELETE THIS BEFORE PUSHING TO GITHUB