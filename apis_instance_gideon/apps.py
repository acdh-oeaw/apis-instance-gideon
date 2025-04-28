from django.apps import AppConfig


class ApisInstanceGideonConfig(AppConfig):
    name = "apis_instance_gideon"

    def ready(self):
        from . import signals  # noqa: F401
