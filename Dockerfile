FROM python

WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    python3-dev \
    default-libmysqlclient-dev \
    gcc \
    libzbar0 \
    && rm -rf /var/lib/apt/lists/*

# Mettre à jour pip
RUN pip install --upgrade pip setuptools wheel

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "appV2_2.py"]