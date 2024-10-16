from django.urls import path, include
from .views import DiagnosisViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r"", DiagnosisViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
