"""Admin configuration for core models."""
from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user_email', 'action', 'resource_type', 'resource_id', 'success']
    list_filter = ['action', 'resource_type', 'success', 'timestamp']
    search_fields = ['user_email', 'resource_id', 'resource_name', 'description']
    readonly_fields = [
        'id', 'timestamp', 'user', 'user_email', 'ip_address', 'user_agent',
        'action', 'resource_type', 'resource_id', 'resource_name',
        'description', 'changes', 'metadata', 'success', 'error_message'
    ]
    ordering = ['-timestamp']
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete audit logs
        return request.user.is_superuser
