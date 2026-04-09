# Build: docker build --build-arg VERSION=1.0.0 -t vpc-stream/dashboard:1.0.0 .
# .dockerignore should exclude: __pycache__, *.pyc, .env, data/, tests/
FROM python:3.11-slim

ARG VERSION=1.0.0
LABEL version="${VERSION}"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY templates/ templates/

RUN groupadd -r appgroup && useradd -r -g appgroup appuser
USER appuser

EXPOSE 5003

CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "--bind", "0.0.0.0:5003", "app:app"]
