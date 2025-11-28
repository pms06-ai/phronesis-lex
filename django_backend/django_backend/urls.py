from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(([
        path("", include("django_backend.cases.urls")),
    ], "api"), namespace="api")),
]
