"""
Core Models for Phronesis LEX
Audit logging and system-level functionality.
"""
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone


class AuditLog(models.Model):
    """
    Audit log for tracking all significant actions in the system.
    Critical for legal compliance and security.
    """
    class Action(models.TextChoices):
        CREATE = 'create', 'Create'
        READ = 'read', 'Read'
        UPDATE = 'update', 'Update'
        DELETE = 'delete', 'Delete'
        LOGIN = 'login', 'Login'
        LOGOUT = 'logout', 'Logout'
        EXPORT = 'export', 'Export'
        ANALYZE = 'analyze', 'Analyze'
        SEARCH = 'search', 'Search'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    # Who
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    user_email = models.EmailField(blank=True, null=True)  # Preserved even if user deleted
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)

    # What
    action = models.CharField(max_length=20, choices=Action.choices, db_index=True)
    resource_type = models.CharField(max_length=50, db_index=True)  # e.g., 'case', 'document'
    resource_id = models.CharField(max_length=100, blank=True, null=True)
    resource_name = models.CharField(max_length=255, blank=True, null=True)

    # Details
    description = models.TextField(blank=True, null=True)
    changes = models.JSONField(default=dict, blank=True)  # Before/after for updates
    metadata = models.JSONField(default=dict, blank=True)

    # Result
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp', 'action']),
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['user', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.timestamp}: {self.user_email or 'Anonymous'} {self.action} {self.resource_type}"

    @classmethod
    def log(cls, request, action, resource_type, resource_id=None, resource_name=None,
            description=None, changes=None, metadata=None, success=True, error_message=None):
        """
        Create an audit log entry.

        Usage:
            AuditLog.log(
                request=self.request,
                action=AuditLog.Action.CREATE,
                resource_type='case',
                resource_id=str(case.id),
                resource_name=case.reference,
                description='Created new case'
            )
        """
        user = request.user if request and hasattr(request, 'user') and request.user.is_authenticated else None

        return cls.objects.create(
            user=user,
            user_email=user.email if user else None,
            ip_address=cls._get_client_ip(request) if request else None,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500] if request else None,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            resource_name=resource_name,
            description=description,
            changes=changes or {},
            metadata=metadata or {},
            success=success,
            error_message=error_message,
        )

    @staticmethod
    def _get_client_ip(request):
        """Extract client IP from request."""
        if not request:
            return None
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
