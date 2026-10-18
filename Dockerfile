FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home app && mkdir /data && chown app:app /data
COPY backend ./backend
COPY frontend ./frontend
USER app
ENV SIMPLECATER_DB=/data/simplecater.db
EXPOSE 8000
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
