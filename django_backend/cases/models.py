"""Models for the Cases domain."""
import uuid
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

class Case(models.Model):
    """Represents a legal case (maps to existing `cases` table)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=512, blank=True, null=True)
    court = models.CharField(max_length=255, blank=True, null=True)

    FAMILY = "family"
    CIVIL = "civil"
    CRIMINAL = "criminal"
    TRIBUNAL = "tribunal"
    OTHER = "other"

    CASE_TYPES = [
        (FAMILY, "Family"),
        (CIVIL, "Civil"),
        (CRIMINAL, "Criminal"),
        (TRIBUNAL, "Tribunal"),
        (OTHER, "Other"),
    ]

    case_type = models.CharField(max_length=20, choices=CASE_TYPES, default=FAMILY)

    ACTIVE = "active"
    CLOSED = "closed"
    APPEAL = "appeal"
    ARCHIVED = "archived"

    STATUS_CHOICES = [
        (ACTIVE, "Active"),
        (CLOSED, "Closed"),
        (APPEAL, "On Appeal"),
        (ARCHIVED, "Archived"),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=ACTIVE)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    # Flexible extra data
    metadata = models.JSONField(blank=True, null=True)

    class Meta:
        db_table = "cases"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reference} ({self.title or 'Untitled'})"
