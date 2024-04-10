import django

PROJECT_APPS = (
    "testapp",
    "django_conditions",
)

INSTALLED_APPS = (
    "django.contrib.contenttypes",
    "django.contrib.auth",
) + PROJECT_APPS

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",  # this is default
)

DATABASE_ENGINE = "sqlite3"
SECRET_KEY = "nokey"
MIDDLEWARE_CLASSES = ()
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
    }
}

MIGRATION_MODULES = {
    "auth": None,
    "contenttypes": None,
    "guardian": None,
}


ANONYMOUS_USER_ID = 0

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
