from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import UserSerializer, UserDetailSerializer
from .models import User
from utils.tokenManagement import (
    get_tokens_for_user,
)  # Asegúrate de importar correctamente la función
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from apps.sign.permissions import IsSuperAdmin, IsConsultor, IsAdmin, GroupTypes
from django.contrib.auth.models import Group


@api_view(["POST"])
@authentication_classes([JWTAuthentication])  #
def login(request):
    try:
        user = User.objects.get(email=request.data["email"])
    except User.DoesNotExist:
        return Response(
            {"error": "Este usuario no se encuentra registrado o esta inactivo"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not user.is_active:
        return Response(
            {"error": "Este usuario no se encuentra registrado o esta inactivo"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not user.check_password(request.data["password"]):
        return Response(
            {"error": "Credenciales inválidas"}, status=status.HTTP_400_BAD_REQUEST
        )

    refresh = get_tokens_for_user(user)
    serializer = UserDetailSerializer(user)  # Ajusta según tu serializador de usuario
    return Response(
        {"tokens": refresh, "user": serializer.data}, status=status.HTTP_200_OK
    )


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])  # Requiere autenticación JWT
def register(request):
    try:
        if IsAdmin().has_permission(request.user) or IsSuperAdmin().has_permission(
            request.user
        ):
            password = request.data.get("password")
            serializer = UserSerializer(data=request.data)
            groups = request.data.get("groups", [])
            if serializer.is_valid():
                serializer.save()
                user = User.objects.get(username=serializer.data["username"])
                user.set_password(password)
                user.groups.set(groups)
                user.save()
                # Genera tokens para el usuario registrado
                refresh = RefreshToken.for_user(user)
                tokens = {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }
                return Response(
                    {"tokens": tokens, "user": serializer.data},
                    status=status.HTTP_201_CREATED,
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response(
                {"error": "No tienes los privilegios para esta operacion"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
    except Exception as ex:
        return Response(
            {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])  # Requiere autenticación JWT
def profile(request):
    try:
        user = request.user
        serializer = UserDetailSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as ex:
        return Response(
            {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])  # Requiere autenticación JWT
def findAllConsultants(request):
    try:
        consultor_group = Group.objects.get(name=GroupTypes.CONSULTOR.value)
        users = User.objects.filter(groups=consultor_group)
        serializer = UserDetailSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as ex:
        return Response(
            {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
