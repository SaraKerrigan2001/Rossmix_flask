# Usa una imagen oficial de Python como base
FROM python:3.11-slim

# Establece el directorio de trabajo en /app
WORKDIR /app

# Establece variables de entorno
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Instala dependencias del sistema requeridas
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Instala las dependencias de Python
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copia los archivos del proyecto al contenedor
COPY . /app/

# Expone el puerto que usa Flask/Gunicorn
EXPOSE 5000

# Ejecuta Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "wsgi:app"]
