FROM python:3.12.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/src:/app/backend WEB_CONCURRENCY=1
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home --uid 10001 marie
COPY src/marieSimulator /app/src/marieSimulator
COPY backend/marie_api /app/backend/marie_api
USER marie
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=2)"
CMD ["python", "-m", "uvicorn", "marie_api.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-access-log", "--limit-concurrency", "150", "--timeout-keep-alive", "5"]
