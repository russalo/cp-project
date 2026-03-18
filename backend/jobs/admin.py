from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Job


@admin.register(Job)
class JobAdmin(ModelAdmin):
    list_display = ('job_number', 'name', 'gc_name', 'location', 'active')
    list_filter = ('active',)
    search_fields = ('job_number', 'name', 'gc_name', 'location')
