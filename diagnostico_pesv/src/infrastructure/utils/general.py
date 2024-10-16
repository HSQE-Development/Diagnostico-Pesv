import base64
import os
from django.conf import settings
import uuid


def save_avatar(base64_string):
    # Decodifica la cadena base64
    try:
        format, imgstr = base64_string.split(";base64,")
        ext = format.split("/")[-1]  # Obtiene la extensión del archivo
        data = base64.b64decode(imgstr)  # Decodifica el string base64
        id = uuid.uuid4().hex[:10]
        # Define la ruta donde se guardará el archivo
        filename = f"{id}_avatar.{ext}"
        file_path = os.path.join(settings.MEDIA_ROOT, "avatars", filename)

        # Crea la carpeta si no existe
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Guarda el archivo
        with open(file_path, "wb") as f:
            f.write(data)

        return f"avatars/{filename}"
    except Exception as e:
        raise (f"Error guardando avatar: {e}")
