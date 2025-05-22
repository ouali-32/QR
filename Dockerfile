FROM python:3.9-slim

WORKDIR /app

# Installation des dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    python3-dev \
    default-libmysqlclient-dev \
    gcc \
    libzbar0 \
    pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Mise à jour de pip et installation des outils de base
RUN pip install --upgrade pip setuptools wheel

# Copie et installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie des fichiers de l'application
COPY . .

# Exposition du port
EXPOSE 5000

# Commande de démarrage
CMD ["python", "appV2_2.py"]
