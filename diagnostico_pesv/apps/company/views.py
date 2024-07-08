from django.shortcuts import render
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import CompanySerializer
from .models import Company, Segments
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404
import logging

logger = logging.getLogger(__name__)
# Create your views here.
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])  # Requiere autenticación JWT
def findAll(request:Request):
    """
    Consulta todos los datos segun el criterio del filter
    """
    try:
        companies = Company.objects.filter(deleted_at=None)
        serializer = CompanySerializer(companies, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as ex:
        logger.error(f"Error en findAll: {str(ex)}")
        return Response({"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])  # Requiere autenticación JWT
def findById(request:Request, id):
    """
    Consulta segun el id proporcionado en la url
    """
    try:
        company = Company.objects.get(pk=id)
        serializer = CompanySerializer(company)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as ex:
        return Response({"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['PATCH'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])  # Requiere autenticación JWT
def update(request:Request):
    """
    Actualiza segun el id proporcionado en el body del cuerpoo, el ID no se pide en la url
    """
    try:
        id = request.data.get("id")
        if id is None:
            return Response({"error": "No se proporciona el id que se va a actualizar"}, status=status.HTTP_400_BAD_REQUEST)
        
        name = request.data.get("name")
        nit = request.data.get("nit")
        size = request.data.get("size")
        segment_id = request.data.get("segment")
        dependant = request.data.get("dependant")
        dependant_phone = request.data.get("dependant_phone")
        activities_ciiu = request.data.get("activities_ciiu")
        email = request.data.get("email")
        acquired_certification = request.data.get("acquired_certification")
        diagnosis = request.data.get("diagnosis")
        
        company = get_object_or_404(Company, id=id)
        
        if name is not None:
            company.name = name
        if nit is not None:
            company.nit = nit
        if size is not None:
            company.size = size
        if segment_id is not None:
            company.segment_id = segment_id
        if dependant is not None:
            company.dependant = dependant
        if dependant_phone is not None:
            company.dependant_phone = dependant_phone
        if activities_ciiu is not None:
            company.activities_ciiu = activities_ciiu
        if email is not None:
            company.email = email
        if acquired_certification is not None:
            company.acquired_certification = acquired_certification
        if diagnosis is not None:
            company.diagnosis = diagnosis
        
        company.save()
        serializer = CompanySerializer(company)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as ex:
        return Response({"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    
@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])  # Requiere autenticación JWT
def delete(request:Request, id):
    """
    Elimina segun el id proporcionado en la url, se usa soft deletes, osea no elimina el registro como tal
    """
    try:
        company = get_object_or_404(Company, pk=id)
        company.delete()
        serializer = CompanySerializer(company)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as ex:
        return Response({"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    