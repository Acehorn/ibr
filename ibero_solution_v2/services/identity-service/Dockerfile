FROM python:3.11-slim
WORKDIR /app
COPY services/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY . /app
ENV PYTHONPATH=/app
CMD ["uvicorn", "main:app", "--app-dir", "/app/services/identity-service/app", "--host", "0.0.0.0", "--port", "8001"]
