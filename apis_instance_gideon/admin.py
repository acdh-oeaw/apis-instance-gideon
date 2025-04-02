from django.contrib import admin
from apis_instance_gideon.models import Person


@admin.register(Person)
class GideonAdmin(admin.ModelAdmin):
    pass
