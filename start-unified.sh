#!/bin/bash
# Unified startup script for Automotive Chatbot Platform
# Manages startup order and health checks for all services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✓${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ✗${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠${NC} $1"
}

# Health check function
check_service() {
    local service_name=$1
    local url=$2
    local max_attempts=$3
    local attempt=1
    
    log "Checking $service_name health at $url..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$url" > /dev/null 2>&1; then
            log_success "$service_name is healthy (attempt $attempt/$max_attempts)"
            return 0
        fi
        
        log_warning "$service_name not ready, attempt $attempt/$max_attempts"
        sleep 5
        ((attempt++))
    done
    
    log_error "$service_name failed health check after $max_attempts attempts"
    return 1
}

# Wait for service to be ready
wait_for_service() {
    local service_name=$1
    local port=$2
    local max_attempts=$3
    local attempt=1
    
    log "Waiting for $service_name on port $port..."
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z localhost $port 2>/dev/null; then
            log_success "$service_name is listening on port $port"
            return 0
        fi
        
        log_warning "$service_name not ready on port $port, attempt $attempt/$max_attempts"
        sleep 3
        ((attempt++))
    done
    
    log_error "$service_name failed to start on port $port after $max_attempts attempts"
    return 1
}

# Create necessary directories
log "Creating application directories..."
mkdir -p /app/logs /app/cache /app/uploads
chown -R appuser:appuser /app/logs /app/cache /app/uploads 2>/dev/null || true

# Start Redis first
log "Starting Redis server..."
redis-server /etc/redis/redis.conf &
REDIS_PID=$!

# Wait for Redis to be ready
if wait_for_service "Redis" 6379 20; then
    log_success "Redis started successfully"
else
    log_error "Failed to start Redis"
    exit 1
fi

# Start Backend (FastAPI)
log "Starting Backend (FastAPI)..."
cd /app/backend
export PYTHONPATH="/app/backend"
export PYTHONUNBUFFERED=1
/app/venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 2 &
BACKEND_PID=$!

# Wait for Backend to be ready
if wait_for_service "Backend" 8000 30; then
    if check_service "Backend" "http://localhost:8000/health" 10; then
        log_success "Backend started successfully"
    else
        log_error "Backend health check failed"
        exit 1
    fi
else
    log_error "Failed to start Backend"
    exit 1
fi

# Start RASA server
log "Starting RASA server..."
cd /app/rasa
/app/rasa-venv/bin/rasa run --enable-api --cors "*" --port 5005 &
RASA_PID=$!

# Start RASA Actions server
log "Starting RASA Actions server..."
/app/rasa-venv/bin/rasa run actions --port 5055 &
RASA_ACTIONS_PID=$!

# Wait for RASA to be ready
if wait_for_service "RASA" 5005 30; then
    log_success "RASA started successfully"
else
    log_error "Failed to start RASA"
    exit 1
fi

if wait_for_service "RASA Actions" 5055 30; then
    log_success "RASA Actions started successfully"
else
    log_warning "RASA Actions may not be available"
fi

# Start Frontend (Next.js)
log "Starting Frontend (Next.js)..."
cd /app/frontend
export NODE_ENV=production
export PORT=3000
export HOSTNAME="0.0.0.0"
node server.js &
FRONTEND_PID=$!

# Wait for Frontend to be ready
if wait_for_service "Frontend" 3000 30; then
    log_success "Frontend started successfully"
else
    log_error "Failed to start Frontend"
    exit 1
fi

# Start Nginx
log "Starting Nginx..."
nginx -t && nginx -g "daemon off;" &
NGINX_PID=$!

# Wait for Nginx to be ready
if wait_for_service "Nginx" 80 20; then
    if check_service "Application" "http://localhost/health" 10; then
        log_success "Nginx and application started successfully"
    else
        log_error "Application health check through Nginx failed"
        exit 1
    fi
else
    log_error "Failed to start Nginx"
    exit 1
fi

# Final health checks
log "Performing final health checks..."

# Check all services
services_healthy=true

if ! check_service "Backend API" "http://localhost/api/health" 5; then
    services_healthy=false
fi

if ! check_service "Frontend" "http://localhost/" 5; then
    services_healthy=false
fi

if ! curl -f -s "http://localhost:5005/" > /dev/null 2>&1; then
    log_warning "RASA direct access check failed (may be normal)"
fi

if [ "$services_healthy" = true ]; then
    log_success "All services are healthy and running!"
    log "Application is available at: http://localhost"
    log "API documentation: http://localhost/api/docs"
    log "Health check: http://localhost/health"
else
    log_error "Some services failed health checks"
    exit 1
fi

# Function to handle shutdown
shutdown() {
    log "Shutting down services..."
    
    # Kill all background processes
    [ ! -z "$NGINX_PID" ] && kill $NGINX_PID 2>/dev/null || true
    [ ! -z "$FRONTEND_PID" ] && kill $FRONTEND_PID 2>/dev/null || true
    [ ! -z "$RASA_ACTIONS_PID" ] && kill $RASA_ACTIONS_PID 2>/dev/null || true
    [ ! -z "$RASA_PID" ] && kill $RASA_PID 2>/dev/null || true
    [ ! -z "$BACKEND_PID" ] && kill $BACKEND_PID 2>/dev/null || true
    [ ! -z "$REDIS_PID" ] && kill $REDIS_PID 2>/dev/null || true
    
    log_success "All services stopped"
    exit 0
}

# Set up signal handlers
trap shutdown SIGTERM SIGINT

# Keep the script running and monitor services
log "Monitoring services... Press Ctrl+C to stop"

while true; do
    sleep 30
    
    # Check if critical services are still running
    if ! kill -0 $NGINX_PID 2>/dev/null; then
        log_error "Nginx process died, restarting..."
        nginx -g "daemon off;" &
        NGINX_PID=$!
    fi
    
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        log_error "Backend process died, restarting..."
        cd /app/backend
        /app/venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 2 &
        BACKEND_PID=$!
    fi
    
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        log_error "Frontend process died, restarting..."
        cd /app/frontend
        node server.js &
        FRONTEND_PID=$!
    fi
    
    # Perform periodic health checks
    if ! check_service "Application" "http://localhost/health" 1; then
        log_warning "Application health check failed during monitoring"
    fi
done