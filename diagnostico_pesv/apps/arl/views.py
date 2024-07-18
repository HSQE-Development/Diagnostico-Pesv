from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import *
from .serializers import *
from utils import functionUtils
import logging

logger = logging.getLogger(__name__)


# Create your views here.
@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])  # Requiere autenticación JWT
def findAll(request: Request):
    try:
        arls: Arl = Arl.objects.all()
        serializer = ArlSerializer(arls, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as ex:
        logger.error(f"Error en findAll: {str(ex)}")
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
        arl = Arl.objects.get(pk=id)
        serializer = ArlSerializer(arl)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as ex:
        return Response(
            {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])  # Requiere autenticación JWT
def save(request: Request):
    try:
        name = functionUtils.eliminar_tildes(request.data.get("name"))

        if Arl.objects.filter(name__iexact=name).exists():
            return Response(
                {"error": "Esta arl ya existe"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = ArlSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as ex:
        return Response(
            {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["PATCH"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])  # Requiere autenticación JWT
def update(request: Request):
    """
    Actualiza segun el id proporcionado en el body del cuerpoo, el ID no se pide en la url
    """
    try:
        id = request.data.get("id")
        if id is None:
            return Response(
                {"error": "No se proporciona el id que se va a actualizar"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        name = request.data.get("name")
        arl = Arl.objects.get(pk=id)

        if name is not None:
            arl.name = name

        arl.save()
        serializer = ArlSerializer(arl)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as ex:
        return Response(
            {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["DELETE"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])  # Requiere autenticación JWT
def delete(request: Request, id):
    """
    Elimina segun el id proporcionado en la url, se usa soft deletes, osea no elimina el registro como tal
    """
    try:
        arl = Arl.objects.get(pk=id)
        arl.delete()
        serializer = ArlSerializer(arl)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as ex:
        return Response(
            {"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
