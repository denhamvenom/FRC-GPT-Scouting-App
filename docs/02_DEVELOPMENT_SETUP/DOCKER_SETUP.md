# Docker Setup and Configuration

**Purpose**: Comprehensive Docker containerization guide  
**Audience**: Developers, DevOps engineers, and deployment teams  
**Scope**: Development, testing, and production Docker configurations  

---

## Docker Overview

Docker containerization provides **consistent environments** across development, testing, and production while enabling **easy scaling** and **simplified deployment**. The FRC GPT Scouting App uses a multi-container architecture with specialized containers for each service.

### Container Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    DOCKER COMPOSE STACK                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Frontend   │  │   Backend   │  │   Nginx     │        │
│  │ Container   │  │ Container   │  │ Container   │        │
│  │             │  │             │  │             │        │
│  │ React Build │  │ FastAPI     │  │ Reverse     │        │
│  │ Static Srv  │  │ + Services  │  │ Proxy       │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                           │
│  ┌─────────────┐  ┌─────────────┐                        │
│  │  Database   │  │    Redis    │                        │
│  │ Container   │  │ Container   │                        │
│  │             │  │             │                        │
│  │ SQLite/     │  │ Cache &     │                        │
│  │ PostgreSQL  │  │ Sessions    │                        │
│  └─────────────┘  └─────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Docker Configurations

### Development Configuration (`docker-compose.dev.yml`)

**Purpose**: Fast development with hot reloading and debugging

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - /app/venv  # Exclude virtual environment
    environment:
      - ENVIRONMENT=development
      - DEBUG=true
      - LOG_LEVEL=DEBUG
      - DATABASE_URL=sqlite:///./app/data/scouting_app.db
      - FRONTEND_URL=http://localhost:3000
    env_file:
      - backend/.env
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    depends_on:
      - redis
    networks:
      - app-network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules  # Exclude node_modules
    environment:
      - VITE_API_URL=http://localhost:8000
      - VITE_DEBUG_MODE=true
    command: npm run dev -- --host 0.0.0.0
    depends_on:
      - backend
    networks:
      - app-network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    networks:
      - app-network

volumes:
  redis_data:

networks:
  app-network:
    driver: bridge
```

### Production Configuration (`docker-compose.prod.yml`)

**Purpose**: Optimized production deployment with security and performance

```yaml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - static_files:/usr/share/nginx/html/static
    depends_on:
      - backend
      - frontend
    networks:
      - app-network
    restart: unless-stopped

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    expose:
      - "8000"
    volumes:
      - ./backend/app/data:/app/data
      - logs:/app/logs
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
      - LOG_LEVEL=INFO
      - DATABASE_URL=postgresql://user:pass@postgres:5432/scouting_app
    env_file:
      - backend/.env.prod
    command: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
    depends_on:
      - postgres
      - redis
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    volumes:
      - static_files:/app/dist
    networks:
      - app-network
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=scouting_app
      - POSTGRES_USER=scouting_user
      - POSTGRES_PASSWORD_FILE=/run/secrets/postgres_password
    secrets:
      - postgres_password
    networks:
      - app-network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes --requirepass-file /run/secrets/redis_password
    secrets:
      - redis_password
    networks:
      - app-network
    restart: unless-stopped

secrets:
  postgres_password:
    file: ./secrets/postgres_password.txt
  redis_password:
    file: ./secrets/redis_password.txt

volumes:
  postgres_data:
  redis_data:
  static_files:
  logs:

networks:
  app-network:
    driver: bridge
```

---

## Dockerfile Configurations

### Backend Development Dockerfile (`backend/Dockerfile.dev`)

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app
USER app

# Copy application code
COPY --chown=app:app . .

# Create data directory
RUN mkdir -p app/data

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Development command (overridden in docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### Backend Production Dockerfile (`backend/Dockerfile.prod`)

```dockerfile
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/app/.local

# Copy application code
COPY --chown=app:app . .

# Create necessary directories
RUN mkdir -p app/data logs && chown -R app:app app/data logs

# Switch to non-root user
USER app

# Add local packages to PATH
ENV PATH=/home/app/.local/bin:$PATH

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production command
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
```

### Frontend Development Dockerfile (`frontend/Dockerfile.dev`)

```dockerfile
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001

# Copy source code
COPY --chown=nextjs:nodejs . .

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/ || exit 1

# Development command
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

### Frontend Production Dockerfile (`frontend/Dockerfile.prod`)

```dockerfile
FROM node:18-alpine AS builder

# Set working directory
WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built application
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Create non-root user for nginx
RUN addgroup -g 1001 -S nginx
RUN adduser -D -S -u 1001 nginx nginx

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
```

---

## Nginx Configuration

### Development Nginx (`nginx/nginx.dev.conf`)

```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:3000;
    }

    server {
        listen 80;
        server_name localhost;

        # Frontend proxy
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket support for Vite HMR
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        # API proxy
        location /api {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check
        location /health {
            proxy_pass http://backend/health;
        }
    }
}
```

### Production Nginx (`nginx/nginx.prod.conf`)

```nginx
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    access_log /var/log/nginx/access.log main;

    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript 
               application/javascript application/xml+rss 
               application/json;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

    upstream backend {
        server backend:8000;
        keepalive 32;
    }

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    server {
        listen 80;
        server_name your-domain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

        # Static files
        location / {
            root /usr/share/nginx/html;
            index index.html index.htm;
            try_files $uri $uri/ /index.html;

            # Cache static assets
            location ~* \.(css|js|jpg|jpeg|png|gif|ico|svg)$ {
                expires 1y;
                add_header Cache-Control "public, immutable";
            }
        }

        # API proxy with rate limiting
        location /api {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts
            proxy_connect_timeout 5s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }

        # Health check (no rate limiting)
        location /health {
            proxy_pass http://backend/health;
            access_log off;
        }
    }
}
```

---

## Environment-Specific Configurations

### Development Environment Setup

**Quick Start**:
```bash
# Clone repository
git clone [repository-url]
cd FRC-GPT-Scouting-App

# Create environment file
cp backend/.env.example backend/.env
# Edit backend/.env with your OpenAI API key

# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f
```

**Development Features**:
- Hot reloading for both frontend and backend
- Debug logging enabled
- Volume mounts for live code editing
- Database persisted in local file
- Redis for development caching

### Testing Environment Setup

**Testing Configuration (`docker-compose.test.yml`)**:
```yaml
version: '3.8'

services:
  backend-test:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    environment:
      - ENVIRONMENT=testing
      - DATABASE_URL=sqlite:///:memory:
      - OPENAI_API_KEY=test-key
    volumes:
      - ./backend:/app
    command: pytest --cov=app --cov-report=xml
    networks:
      - test-network

  frontend-test:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    environment:
      - NODE_ENV=test
    volumes:
      - ./frontend:/app
    command: npm test -- --coverage --watchAll=false
    networks:
      - test-network

networks:
  test-network:
    driver: bridge
```

**Run Tests**:
```bash
# Run all tests
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# Run specific service tests
docker-compose -f docker-compose.test.yml run backend-test
docker-compose -f docker-compose.test.yml run frontend-test
```

### Production Environment Setup

**Prerequisites**:
```bash
# Create production environment file
cp backend/.env.example backend/.env.prod
# Configure production settings

# Create SSL certificates
mkdir -p nginx/ssl
# Add your SSL certificates

# Create secrets
mkdir -p secrets
echo "your-postgres-password" > secrets/postgres_password.txt
echo "your-redis-password" > secrets/redis_password.txt
chmod 600 secrets/*
```

**Production Deployment**:
```bash
# Deploy to production
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f nginx backend
```

---

## Docker Management Commands

### Common Operations

**Start Services**:
```bash
# Development
docker-compose -f docker-compose.dev.yml up -d

# Production
docker-compose -f docker-compose.prod.yml up -d

# Specific service
docker-compose up -d backend
```

**Stop Services**:
```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Stop specific service
docker-compose stop backend
```

**View Logs**:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

**Execute Commands**:
```bash
# Enter container shell
docker-compose exec backend bash
docker-compose exec frontend sh

# Run commands
docker-compose exec backend python -m pytest
docker-compose exec frontend npm test
```

### Maintenance Operations

**Update Images**:
```bash
# Pull latest images
docker-compose pull

# Rebuild local images
docker-compose build --no-cache

# Rebuild specific service
docker-compose build backend
```

**Clean Up**:
```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune

# Complete cleanup (careful!)
docker system prune -a
```

**Database Operations**:
```bash
# Backup database
docker-compose exec postgres pg_dump -U scouting_user scouting_app > backup.sql

# Restore database
docker-compose exec -T postgres psql -U scouting_user scouting_app < backup.sql

# Connect to database
docker-compose exec postgres psql -U scouting_user scouting_app
```

---

## Performance Optimization

### Container Resource Limits

**Development Limits** (add to services):
```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
    reservations:
      cpus: '0.5'
      memory: 512M
```

**Production Limits**:
```yaml
deploy:
  resources:
    limits:
      cpus: '4.0'
      memory: 4G
    reservations:
      cpus: '1.0'
      memory: 1G
  restart_policy:
    condition: unless-stopped
    delay: 5s
    max_attempts: 3
```

### Multi-Stage Build Optimization

**Optimized Production Backend**:
```dockerfile
# Use smaller base image
FROM python:3.11-alpine as builder
RUN apk add --no-cache gcc musl-dev
# ... build steps

FROM python:3.11-alpine
RUN apk add --no-cache curl
# ... runtime only
```

### Caching Strategies

**Docker Layer Caching**:
```dockerfile
# Copy requirements first (changes less frequently)
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copy source code last (changes frequently)
COPY . .
```

**Build Cache**:
```bash
# Use BuildKit for better caching
export DOCKER_BUILDKIT=1
docker build --build-arg BUILDKIT_INLINE_CACHE=1 .
```

---

## Security Best Practices

### Container Security

**Non-Root Users**:
```dockerfile
# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app
```

**Read-Only Root Filesystem**:
```yaml
security_opt:
  - no-new-privileges:true
read_only: true
tmpfs:
  - /tmp
  - /var/cache
```

**Secrets Management**:
```yaml
secrets:
  api_key:
    file: ./secrets/openai_api_key.txt
  db_password:
    external: true
```

### Network Security

**Custom Networks**:
```yaml
networks:
  frontend-network:
    driver: bridge
  backend-network:
    driver: bridge
    internal: true  # No external access
```

**Service Isolation**:
```yaml
services:
  backend:
    networks:
      - backend-network
      - frontend-network
  
  postgres:
    networks:
      - backend-network  # Only backend access
```

---

## Monitoring and Health Checks

### Health Check Configuration

**Backend Health Check**:
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

**Custom Health Check Script**:
```bash
#!/bin/bash
# health-check.sh
set -e

# Check API health
curl -f http://localhost:8000/health

# Check database connection
python -c "from app.database import test_connection; test_connection()"

# Check AI service
curl -f http://localhost:8000/api/health/ai
```

### Monitoring with Docker Stats

**Resource Monitoring**:
```bash
# Monitor all containers
docker stats

# Monitor specific containers
docker stats backend frontend postgres

# Export metrics
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" --no-stream
```

---

## Troubleshooting

### Common Docker Issues

**Port Conflicts**:
```bash
# Check port usage
lsof -i :8000
lsof -i :3000

# Use different ports
docker-compose -f docker-compose.dev.yml up -d --scale backend=0
docker-compose run -p 8001:8000 backend
```

**Permission Issues**:
```bash
# Fix file permissions
sudo chown -R $USER:$USER .

# Fix Docker socket permissions
sudo usermod -aG docker $USER
# Logout and login again
```

**Build Failures**:
```bash
# Clean build cache
docker builder prune

# Build without cache
docker-compose build --no-cache

# Check build logs
docker-compose build backend 2>&1 | tee build.log
```

**Container Startup Issues**:
```bash
# Check container logs
docker-compose logs backend

# Check container status
docker-compose ps

# Inspect container
docker inspect frc-gpt-scouting-app_backend_1
```

**Network Issues**:
```bash
# List networks
docker network ls

# Inspect network
docker network inspect frc-gpt-scouting-app_app-network

# Test connectivity
docker-compose exec backend ping frontend
```

---

## Next Steps

### For Development
1. **[Development Environment](DEVELOPMENT_ENVIRONMENT.md)** - Complete development setup
2. **[Database Setup](DATABASE_INITIALIZATION.md)** - Database configuration
3. **[Testing Guide](../04_DEVELOPMENT_GUIDES/TESTING_GUIDE.md)** - Testing with Docker

### For Production
1. **[Deployment Guide](../06_OPERATIONS/DEPLOYMENT_GUIDE.md)** - Production deployment
2. **[Monitoring](../06_OPERATIONS/MONITORING.md)** - Production monitoring
3. **[Security Guide](../06_OPERATIONS/SECURITY_GUIDE.md)** - Security hardening

### For Scaling
1. **[Performance Optimization](../06_OPERATIONS/PERFORMANCE_OPTIMIZATION.md)** - Scaling strategies
2. **[Load Balancing](../06_OPERATIONS/LOAD_BALANCING.md)** - Multi-instance setup
3. **[Container Orchestration](../06_OPERATIONS/KUBERNETES.md)** - Kubernetes deployment

---

**Last Updated**: June 25, 2025  
**Maintainer**: DevOps Team  
**Related Documents**: [Development Environment](DEVELOPMENT_ENVIRONMENT.md), [Deployment Guide](../06_OPERATIONS/DEPLOYMENT_GUIDE.md)