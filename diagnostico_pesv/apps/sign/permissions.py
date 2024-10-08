from rest_framework.permissions import BasePermission
from apps.sign.models import User
from django.contrib.auth.models import Group
from enum import Enum


class GroupTypes(Enum):
    SUPER_ADMIN = "SuperAdmin"
    ADMIN = "Admin"
    CONSULTOR = "Consultor"


class IsSuperAdmin(BasePermission):
    def has_permission(self, user: User):
        return user and user.groups.filter(name=GroupTypes.SUPER_ADMIN.value).exists()


class IsAdmin(BasePermission):
    def has_permission(self, user: User):
        return user and user.groups.filter(name=GroupTypes.ADMIN.value).exists()


class IsConsultor(BasePermission):
    def has_permission(self, user: User):
        return user and user.groups.filter(name=GroupTypes.CONSULTOR.value).exists()
