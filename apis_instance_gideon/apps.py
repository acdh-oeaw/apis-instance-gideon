from django.apps import AppConfig


class ApisInstanceGideonConfig(AppConfig):
    default_auto_field = "django.db.models.AutoField"
    name = "apis_instance_gideon"

    def ready(self):
        from . import signals  # noqa: F401
