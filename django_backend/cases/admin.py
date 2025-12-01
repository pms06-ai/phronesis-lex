"""Admin configuration for cases app."""
from django.contrib import admin
from .models import Case


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ['id', 'reference', 'title', 'court', 'case_type', 'status', 'created_at']
    list_filter = ['case_type', 'status']
    search_fields = ['reference', 'title', 'court']
    readonly_fields = ['id', 'created_at', 'updated_at']
