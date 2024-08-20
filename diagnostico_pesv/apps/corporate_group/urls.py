from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CorporateGroupViewSet

router = DefaultRouter()
router.register(r"", CorporateGroupViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
