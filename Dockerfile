FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de requisitos
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar archivos del proyecto
COPY . .

# Crear carpetas necesarias
RUN mkdir -p documentos_financieros chroma_db

# Exponer puerto de Chainlit
EXPOSE 7860

# Variables de entorno
ENV CHAINLIT_HOST=0.0.0.0
ENV CHAINLIT_PORT=7860

# Comando para ejecutar la aplicación
CMD ["chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "7860"]