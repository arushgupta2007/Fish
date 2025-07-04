# Half Suit Card Game - Deployment Guide

## Overview

This guide covers deployment options for the Half Suit online multiplayer card game, including local development, staging, and production environments. The application consists of a FastAPI backend with WebSocket support and a React frontend.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [Local Development](#local-development)
4. [Production Deployment](#production-deployment)
5. [Platform-Specific Deployments](#platform-specific-deployments)
6. [Monitoring and Maintenance](#monitoring-and-maintenance)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software
- Docker and Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.9+ (for local backend development)
- Git

### Account Requirements
- Railway or Render account (for production deployment)
- Domain registrar account (optional, for custom domain)

## Environment Configuration

### Backend Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# Backend Configuration
ENVIRONMENT=production
DEBUG=false
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=["https://yourfrontend.com"]

# Security
SECRET_KEY=your-super-secret-key-change-in-production
ALLOWED_HOSTS=["yourdomain.com", "*.railway.app", "*.render.com"]

# WebSocket Configuration
WEBSOCKET_MAX_CONNECTIONS=1000
WEBSOCKET_PING_INTERVAL=30
WEBSOCKET_PING_TIMEOUT=10

# Game Configuration
MAX_GAMES=100
GAME_TIMEOUT_MINUTES=60
INACTIVE_GAME_CLEANUP_MINUTES=120

# Optional: Database (for future persistence)
# DATABASE_URL=postgresql://user:pass@host:port/db
# REDIS_URL=redis://user:pass@host:port/db
```

### Frontend Environment Variables

Create a `.env` file in the `frontend/` directory:

```bash
# API Configuration
VITE_API_BASE_URL=https://your-backend-url.com
VITE_WS_BASE_URL=wss://your-backend-url.com

# Environment
VITE_ENVIRONMENT=production
VITE_DEBUG=false

# Game Configuration
VITE_RECONNECT_ATTEMPTS=5
VITE_RECONNECT_DELAY=3000
```

## Local Development

### Using Docker Compose (Recommended)

1. **Clone the repository**:
```bash
git clone <repository-url>
cd half-suit-game
```

2. **Create environment files**:
```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

3. **Start the development environment**:
```bash
docker-compose up -d
```

4. **Access the application**:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Manual Setup

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## Production Deployment

### Build Process

#### Backend Build
```bash
cd backend
# Install dependencies
pip install -r requirements.txt

# Optional: Run tests
python -m pytest

# The FastAPI app is ready to deploy
```

#### Frontend Build
```bash
cd frontend
# Install dependencies
npm install

# Build for production
npm run build

# The build files will be in the 'dist' directory
```

### Docker Production Build

#### Backend Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY config.py .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Frontend Dockerfile
```dockerfile
FROM node:18-alpine as builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## Platform-Specific Deployments

### Railway Deployment

#### Backend on Railway

1. **Create a new Railway project**:
```bash
railway login
railway init
railway add
```

2. **Configure environment variables** in Railway dashboard:
- Add all backend environment variables
- Set `PORT` to Railway's provided port
- Set `CORS_ORIGINS` to include your frontend URL

3. **Deploy**:
```bash
railway up
```

#### Frontend on Railway

1. **Create separate Railway service**:
```bash
railway init
railway add
```

2. **Add build and start commands** in Railway dashboard:
- Build Command: `npm run build`
- Start Command: `npm run preview`

3. **Configure environment variables**:
- Set `VITE_API_BASE_URL` to your backend Railway URL
- Set `VITE_WS_BASE_URL` to your backend Railway WebSocket URL

### Render Deployment

#### Backend on Render

1. **Create a new Web Service**:
- Repository: Connect your GitHub repo
- Branch: `main`
- Root Directory: `backend`
- Environment: `Python 3`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

2. **Configure environment variables** in Render dashboard

#### Frontend on Render

1. **Create a new Static Site**:
- Repository: Connect your GitHub repo
- Branch: `main`
- Root Directory: `frontend`
- Build Command: `npm install && npm run build`
- Publish Directory: `dist`

2. **Configure environment variables** in Render dashboard

### Vercel Deployment (Frontend Only)

1. **Install Vercel CLI**:
```bash
npm install -g vercel
```

2. **Deploy from frontend directory**:
```bash
cd frontend
vercel --prod
```

3. **Configure environment variables** in Vercel dashboard

## SSL/HTTPS Configuration

### Let's Encrypt with Nginx

If deploying to a custom server:

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # WebSocket
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Monitoring and Maintenance

### Health Checks

#### Backend Health Check Endpoint
```python
# Add to backend/app/main.py
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
```

#### Frontend Health Check
```javascript
// Add to frontend/src/services/api.js
export const healthCheck = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    return response.ok;
  } catch (error) {
    return false;
  }
};
```

### Logging

#### Backend Logging
```python
# Add to backend/app/config.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
```

#### Frontend Error Tracking
```javascript
// Add to frontend/src/utils/errorHandler.js
export const logError = (error, context) => {
  console.error('Error:', error, 'Context:', context);
  // Add external error tracking service integration here
};
```

### Performance Monitoring

#### Backend Metrics
- Monitor WebSocket connection count
- Track active games
- Monitor memory usage
- Track API response times

#### Frontend Metrics
- Monitor page load times
- Track WebSocket connection stability
- Monitor user interactions

## Troubleshooting

### Common Issues

#### WebSocket Connection Failures
- Check CORS configuration
- Verify WebSocket URL (wss:// for HTTPS)
- Check firewall settings
- Verify SSL certificate for secure connections

#### High Memory Usage
- Implement game cleanup for inactive games
- Monitor WebSocket connection leaks
- Use connection pooling

#### Game State Sync Issues
- Implement retry logic for failed WebSocket messages
- Add heartbeat mechanism
- Implement reconnection with state recovery

### Debug Commands

#### Backend Debug
```bash
# Check logs
docker logs <backend-container-id>

# Access container
docker exec -it <backend-container-id> /bin/bash

# Test WebSocket connection
wscat -c ws://localhost:8000/ws
```

#### Frontend Debug
```bash
# Check build output
npm run build

# Analyze bundle size
npm run analyze

# Test production build locally
npm run preview
```

### Performance Optimization

#### Backend Optimizations
- Use async/await for all I/O operations
- Implement connection pooling
- Use Redis for session management (future enhancement)
- Implement rate limiting

#### Frontend Optimizations
- Code splitting for large components
- Lazy loading for non-critical components
- WebSocket message batching
- Implement service worker for offline support

## Security Considerations

### Production Security Checklist

- [ ] Change default secret keys
- [ ] Enable HTTPS/WSS
- [ ] Configure CORS properly
- [ ] Implement rate limiting
- [ ] Set up proper firewall rules
- [ ] Regular security updates
- [ ] Monitor for suspicious activity
- [ ] Implement input validation
- [ ] Use secure headers
- [ ] Regular backup procedures

### Environment Security

```bash
# Backend security headers
SECURE_HEADERS_ENABLED=true
HSTS_MAX_AGE=31536000
CONTENT_SECURITY_POLICY="default-src 'self'"

# Rate limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

## Scaling Considerations

### Horizontal Scaling
- Use load balancer for multiple backend instances
- Implement sticky sessions for WebSocket connections
- Use Redis for shared game state (future enhancement)
- Implement database clustering (future enhancement)

### Vertical Scaling
- Monitor CPU and memory usage
- Optimize game state storage
- Implement efficient data structures
- Use connection pooling

## Backup and Recovery

### Game State Backup
```python
# Implement in backend/app/utils/backup.py
async def backup_active_games():
    # Export active game states
    # Store in persistent storage
    pass

async def restore_games():
    # Restore game states from backup
    # Reconnect active players
    pass
```

### Disaster Recovery Plan
1. Monitor service health
2. Implement automatic failover
3. Regular backup procedures
4. Document recovery procedures
5. Test recovery procedures regularly

## Support and Maintenance

### Regular Maintenance Tasks
- Monitor system resources
- Update dependencies
- Review security logs
- Clean up inactive games
- Monitor WebSocket connections
- Update SSL certificates

### Support Contacts
- Technical Issues: Create GitHub issues
- Security Issues: security@yourdomain.com
- General Support: support@yourdomain.com

---

For additional help, refer to the [API Documentation](API.md) and [Development Guide](DEVELOPMENT.md).