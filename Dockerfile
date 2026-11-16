FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -e . && useradd -m appuser
USER appuser
CMD ["uvicorn", "modelroi.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
