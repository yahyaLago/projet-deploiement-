# Image de MaintAI : le code et ses bibliothèques, sans les données ni le modèle.
# Construire : docker build -t maintai:0.4.0 .

FROM python:3.11-slim

WORKDIR /app

# Les bibliothèques avant le code : cette étape lente reste en cache
# tant que requirements-docker.txt ne change pas.
COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

COPY maintai maintai
COPY ui ui

ENV MAINTAI_MODELS_DIR=/app/models
ENV MAINTAI_DATA_PATH=/app/data/sensors.csv

EXPOSE 8000

# 0.0.0.0 : le port publié sur le PC doit joindre le processus dans le conteneur.
# 127.0.0.1 n'écouterait que l'intérieur du conteneur.
CMD ["uvicorn", "maintai.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
