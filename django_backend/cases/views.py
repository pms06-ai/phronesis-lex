from rest_framework import viewsets
from .models import Case
from .serializers import CaseSerializer

class CaseViewSet(viewsets.ModelViewSet):
    """CRUD API for cases. Mirrors the FastAPI endpoints."""

    queryset = Case.objects.all()
    serializer_class = CaseSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        # optional filtering by status / type could be added here
        return qs
