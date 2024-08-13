FROM python:3.12


ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1


# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Copia los archivos de requisitos al contenedor
COPY requirements.txt .

# Actualiza la lista de paquetes y arregla problemas de red
RUN sed -i 's/deb.debian.org/ftp.debian.org/' /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y wget && \
    # Descarga wait-for-it.sh
    wget https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh -O /usr/local/bin/wait-for-it.sh && \
    chmod +x /usr/local/bin/wait-for-it.sh

# Instala las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código fuente del proyecto al contenedor
COPY . .

# Expone el puerto en el que Django correrá
EXPOSE 8000

# Comando para ejecutar el servidor de desarrollo de Django
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "diagnostico_pesv.wsgi:application"]