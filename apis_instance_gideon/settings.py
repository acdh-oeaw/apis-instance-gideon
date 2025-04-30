from apis_acdhch_default_settings.settings import *

INSTALLED_APPS.remove("apis_ontology")
INSTALLED_APPS = ["apis_instance_gideon"] + INSTALLED_APPS

STATIC_ROOT = "/attachments/static"
