"""
URL configuration for diagnostico_pesv project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

API_V = "v1"
API_PREFIX = f"api/{API_V}"

urlpatterns = [
    path("admin/", admin.site.urls),
    path(f"{API_PREFIX}/sign/", include("apps.sign.urls")),
    path(f"{API_PREFIX}/companies/", include("apps.company.urls")),
    path(f"{API_PREFIX}/diagnosis/", include("apps.diagnosis.interfaces.urls")),
    path(f"{API_PREFIX}/arl/", include("apps.arl.urls")),
]
# Con esta linea se puede acceder a los archivos media guardados en el servidor
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
