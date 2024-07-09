from rest_framework import serializers
from .models import User
from django.contrib.auth.models import Group
from utils.base64Image import Base64ImageField


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ["id", "name"]


class UserSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(max_length=None, use_url=True)
    groups = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Group.objects.all(), required=False
    )
    groups_detail = GroupSerializer(source="groups", read_only=True, many=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
            "licensia_sst",
            "cedula",
            "avatar",
            "groups",  # Agrega el campo groups
            "groups_detail",
        ]


class UserDetailSerializer(serializers.ModelSerializer):
    """
    A diferencia de UserSerializer aqui no se muestra el password, usar para temas de consultas
    """

    groups = GroupSerializer(many=True)
    groups = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Group.objects.all(), required=False
    )
    groups_detail = GroupSerializer(source="groups", read_only=True, many=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "licensia_sst",
            "cedula",
            "avatar",
            "groups",
            "groups_detail",
        ]
