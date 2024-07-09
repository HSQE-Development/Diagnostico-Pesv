from rest_framework import serializers
from django.core.files.base import ContentFile
import base64
import uuid


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        # Check if the data is a base64 string
        if isinstance(data, str) and data.startswith("data:image"):
            # Decode the base64 string
            format, imgstr = data.split(";base64,")
            ext = format.split("/")[-1]
            id = uuid.uuid4().hex[:10]
            data = ContentFile(base64.b64decode(imgstr), name=f"{id}.{ext}")
        return super().to_internal_value(data)
