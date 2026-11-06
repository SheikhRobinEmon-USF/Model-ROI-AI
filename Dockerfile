FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir . && useradd -m appuser
USER appuser
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
