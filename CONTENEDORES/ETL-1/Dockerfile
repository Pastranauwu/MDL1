# Usamos una imagen ligera de Python
FROM python:3.9-slim

# Establecemos el directorio de trabajo
WORKDIR /app

# Copiamos el archivo de requerimientos e instalamos las dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto de los archivos de la aplicación
COPY . .

RUN echo "Iniciando el proceso de ETL..."

# Comando para ejecutar el script de ETL
CMD ["python", "etl_processor.py"]
