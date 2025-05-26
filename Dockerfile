# Base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker caching
COPY backend/requirements.txt requirements.txt
COPY backend/requirements-dev.txt requirements-dev.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy the rest of the backend code
COPY backend/ .

# Environment variables
ENV PYTHONPATH=/app
ENV PORT=8000

# Expose the port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]