FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app
COPY backend/seed.py ./seed.py
COPY backend/alembic.ini ./alembic.ini
COPY backend/alembic ./alembic
COPY seed ./seed
COPY storage ./storage
ENV PYTHONPATH=/app
CMD ["sh","-c","alembic upgrade head && python seed.py && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
