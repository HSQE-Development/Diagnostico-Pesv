from django.urls import re_path
from apps.diagnosis.consumers.consumer import DiagnosisConsumer

ws_urlpatterns = [
    re_path(r"ws/diagnosis/$", DiagnosisConsumer.as_asgi()),
]
