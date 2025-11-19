@"
FROM python:3.11-slim

# Installation des outils système
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    curl \
    bc \
    file \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Installation Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gdown

# Téléchargement du TIFF
COPY download_tiff.sh .
RUN chmod +x download_tiff.sh && ./download_tiff.sh

# Copie du code
COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "server:app"]
"@ | Out-File -FilePath Dockerfile -Encoding UTF8 -NoNewline