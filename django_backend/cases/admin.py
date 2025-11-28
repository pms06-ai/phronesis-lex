from django.contrib import admin
from .models import Case

@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ("reference", "title", "court", "case_type", "status", "created_at")
    search_fields = ("reference", "title", "court")
    list_filter = ("case_type", "status")
