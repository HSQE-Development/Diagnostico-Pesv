# coding: utf-8

from django.conf.urls import include
from django.urls import path

from src.infrastructure.api.routes.authorize.routers import UserRouter, AuthRouter
from src.infrastructure.api.views.authorize import UserViewSet, AuthorizeViewSet


user_router = UserRouter()
user_router.register("", viewset=UserViewSet, basename="users")

auth_router = AuthRouter()
auth_router.register("", viewset=AuthorizeViewSet, basename="authorize")


urlpatterns = [
    path("", include(user_router.urls)),
    path("auth/", include(auth_router.urls)),
]
