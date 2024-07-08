from django.shortcuts import render
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import UserSerializer, UserDetailSerializer
from .models import Company, Segments
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication

# Create your views here.
@api_view(['GET'])
@authentication_classes([JWTAuthentication])  #
def findAll(request:Request):
    try:
        companies = Company.objects.filter(deleted_at=None)
        
    except Exception as ex:
        return Response({"error": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)