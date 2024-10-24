from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import (
    UserSerializer,
    UserDetailSerializer,
    GroupSerializer,
    MenuSerializer,
)
from .models import User, Menu
from utils.tokenManagement import (
    get_tokens_for_user,
)  # Asegúrate de importar correctamente la función
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from apps.sign.permissions import IsSuperAdmin, IsAdmin, GroupTypes
from django.contrib.auth.models import Group
import random
import string
from .services import (
    send_temporary_password_email,
    generate_username,
    get_existing_usernames,
)
import traceback
from django.db import transaction


@api_view(["GET"])
@authentication_classes([JWTAuthentication])  #
def findAll(request):
    try:
        users = User.objects.all().order_by("-id")
        serializer = UserDetailSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as ex:
        return Response(
            {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])  # Requiere autenticación JWT
def findById(request: Request, id):
    """
    Consulta segun el id proporcionado en la url
    """
    try:
        user = User.objects.get(pk=id)
        serializer = UserDetailSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as ex:
        return Response(
            {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@authentication_classes([JWTAuthentication])  #
def login(request):
    try:
        user = User.objects.get(email=request.data["email"].strip())
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

    if not user.check_password(request.data["password"].strip()):
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
def logout(request):
    try:
        refresh_token = request.data.get("refresh")
        if refresh_token is None:
            return Response(
                {"error": "Refresh token es requerido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token = RefreshToken(refresh_token)
        token.blacklist()

        return Response(status=status.HTTP_205_RESET_CONTENT)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])  # Requiere autenticación JWT
def register(request):
    try:
        if IsAdmin().has_permission(request.user) or IsSuperAdmin().has_permission(
            request.user
        ):
            cedula = request.data.get("cedula")
            email = request.data.get("email")
            first_name = request.data.get("first_name")
            last_name = request.data.get("last_name")
            groups = request.data.get("groups", [])

            # Verifica si la cédula ya está registrada
            if User.objects.filter(email=email).exists():
                return Response(
                    {"error": "El correo ya está registrado"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if User.objects.filter(cedula=cedula).exists():
                return Response(
                    {"error": "La cédula ya está registrada"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Asignar un nombre de usuario vacío por defecto
            username = request.data.get("username", None)
            if not username:
                request.data["username"] = first_name

            serializer = UserSerializer(data=request.data)
            if serializer.is_valid():
                with transaction.atomic():
                    temp_password = "".join(
                        random.choices(string.ascii_letters + string.digits, k=8)
                    )
                    user = serializer.save()
                    user.set_password(temp_password)
                    user.groups.set(groups)

                    # Generar nombre de usuario único si no se proporcionó
                    if not username:
                        existing_usernames = get_existing_usernames()
                        username = generate_username(
                            first_name,
                            last_name,
                            unique=True,
                            existing_usernames=existing_usernames,
                        )
                        user.username = username

                    user.save()

                    # Enviar correo con la contraseña temporal
                    send_temporary_password_email(user, temp_password)

                    # Genera tokens para el usuario registrado
                    refresh = RefreshToken.for_user(user)
                    tokens = {
                        "refresh": str(refresh),
                        "access": str(refresh.access_token),
                    }

                    return Response(
                        {"tokens": tokens, "user": UserSerializer(user).data},
                        status=status.HTTP_201_CREATED,
                    )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"error": "No tienes los privilegios para esta operación"},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    except Exception as ex:
        tb_str = traceback.format_exc()
        return Response(
            {"error": str(ex), "traceback": tb_str},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
def find_by_id(request: Request):
    try:
        user_id = request.query_params.get("user")
        if user_id:
            user = User.objects.get(pk=user_id)
            serializer = UserDetailSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({}, status=status.HTTP_200_OK)

    except Exception as ex:
        return Response(
            {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["PATCH"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])  # Requiere autenticación JWT
def update(request: Request):
    user_id = request.data.get("id")
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    serializer = UserSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():

        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PATCH"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])  # Requiere autenticación JWT
def change_password(request: Request):
    try:
        user_id = request.data.get("user")
        password = request.data.get("password")
        user = User.objects.get(pk=user_id)
        user.set_password(password)
        user.change_password = True
        user.save()
        serializer = UserDetailSerializer(user)
        return Response(serializer.data)
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


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])  # Requiere autenticación JWT
def findAllGroups(request):
    try:
        groups = Group.objects.all()
        serializer = GroupSerializer(groups, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as ex:
        return Response(
            {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])  # Requiere autenticación JWT
def findMenusByGroups(request: Request):
    try:
        groups_ids = request.query_params.get("groups", "")
        if groups_ids:
            groups_ids = groups_ids.split(",")
        menus = Menu.objects.filter(groups__id__in=groups_ids).distinct()
        serializer = MenuSerializer(menus, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as ex:
        return Response(
            {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
