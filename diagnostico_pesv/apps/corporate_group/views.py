from django.shortcuts import render
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    action,
)
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import status, viewsets
from .models import *
from .serializers import *


# Create your views here.
class CorporateGroupViewSet(viewsets.ModelViewSet):
    queryset = Corporate.objects.all()
    serializer_class = CorporateGroupSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Corporate.objects.all()
