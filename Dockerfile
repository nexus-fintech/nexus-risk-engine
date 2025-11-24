# -------------------------------------------------------------------
# Base Image: Python 3.12 (Slim para menor tamaño)
# -------------------------------------------------------------------
FROM python:3.12-slim

# Metadatos
LABEL maintainer="Angel Cancho <angelcca2001@gmail.com>"

# Evita que Python genere archivos .pyc y fuerza el output a la consola
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Establecemos directorio de trabajo
WORKDIR /app

# Instalamos dependencias del sistema necesarias para compilar algunas librerías de Python
# (gcc, etc.) si fueran necesarias. Para pandas/numpy suele bastar con las precompiladas.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiamos el archivo de requerimientos primero (para aprovechar caché de Docker)
COPY requirements.txt .

# Instalamos las dependencias de Python
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copiamos el código fuente de la aplicación
COPY ./app ./app

# Exponemos el puerto de FastAPI
EXPOSE 8000

# Creamos un usuario no-root para seguridad (opcional pero recomendado)
RUN useradd -m nexususer
USER nexususer

# Comando de inicio usando Uvicorn
# --host 0.0.0.0 es crucial para que Docker exponga el servicio hacia afuera
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]