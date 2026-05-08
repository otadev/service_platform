FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get remove -y gcc \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*
RUN adduser --disabled-password --no-create-home app-user
COPY src/ .
USER app-user
EXPOSE 8000
