# Utiliser une image Python officielle
FROM python:3.12-slim

# Installer uv manuellement
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Définir le répertoire de travail
WORKDIR /app

# Paramètres uv
ENV UV_COMPILE_BYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_MODEL_REPO=""

# Copier les fichiers de dépendances
COPY pyproject.toml uv.lock ./

# Installer les dépendances
RUN /bin/uv sync --frozen --no-install-project --no-dev

# Copier le reste du code
COPY . .
# Installer le projet
RUN /bin/uv sync --frozen --no-dev

EXPOSE 7860

CMD ["/bin/uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]