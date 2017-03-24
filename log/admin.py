from django.contrib import admin
from .models import *


# Register your models here.
class LogAdmin(admin.ModelAdmin):
    list_display = ( 'date', 'description', 'type')

admin.site.register(Log, LogAdmin)