from rest_framework import serializers
from .models import Case

class CaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = [
            "id",
            "reference",
            "title",
            "court",
            "case_type",
            "status",
            "created_at",
            "updated_at",
        ]
