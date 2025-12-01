# Stage 1: Build Frontend
FROM node:20 as frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

# Stage 2: Final Image
FROM python:3.10
WORKDIR /app

# Install dependencies
COPY backend/pyproject.toml .
RUN pip install --upgrade pip
RUN pip install "fastapi[standard]" "uvicorn[standard]" "python-multipart" "email-validator" "passlib[bcrypt]" "tenacity" "pydantic>2.0" "emails" "jinja2" "alembic" "httpx" "psycopg[binary]" "sqlmodel" "bcrypt==4.3.0" "pydantic-settings" "sentry-sdk[fastapi]" "pyjwt" "redis" "minio" "celery[redis]"

# Copy backend code
COPY backend/app /app/app
COPY backend/alembic.ini /app/
COPY backend/scripts /app/scripts

# Copy frontend build
COPY --from=frontend-build /app/frontend/dist /app/static

# Expose port
EXPOSE 8000

# Run command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
