# 🐳 Docker Deployment Guide - Forti-DFIR Web Application

## Quick Start (1 Command)

```bash
cd web_app
docker-compose up --build
```

**That's it!** The application will be available at:
- 🌐 **Frontend**: http://localhost:8080
- 🔗 **Backend API**: http://localhost:8000

## Default Login
- **Username**: `admin`
- **Password**: `admin123`

---

## Detailed Setup

### Prerequisites
- Docker 20.10+ and Docker Compose 2.0+
- 4GB RAM minimum
- 10GB free disk space

### Step 1: Clone and Navigate
```bash
git clone <your-repo>
cd Forti-DFIR/web_app
```

### Step 2: Build and Run
```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up --build -d

# View logs
docker-compose logs -f
```

### Step 3: Access Application
- Open http://localhost:8080 in your browser
- Login with admin/admin123
- Upload and parse your Fortinet logs

---

## Container Services

### Backend Container (`forti-dfir-backend`)
- **Port**: 8000 (maps to 5000 inside container)
- **Base Image**: Python 3.11-slim
- **Features**: Flask API, log parsing, file handling
- **Health Check**: Endpoint monitoring

### Frontend Container (`forti-dfir-frontend`) 
- **Port**: 8080 (maps to 80 inside container)
- **Base Image**: Node 18 → Nginx Alpine
- **Features**: React SPA, API proxy, static file serving

---

## Container Management

### Useful Commands
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up --build

# View container status
docker-compose ps

# View logs
docker-compose logs backend
docker-compose logs frontend

# Execute commands in containers
docker-compose exec backend bash
docker-compose exec frontend sh

# Clean up everything
docker-compose down --volumes --rmi all
```

### Persistent Data
- Upload files: `./backend/uploads/`
- Result files: `./backend/results/`
- Both directories are mounted as volumes

---

## Production Deployment

### 1. Environment Configuration
Create a `.env` file:
```bash
SECRET_KEY=your-super-secret-production-key
JWT_SECRET_KEY=your-jwt-secret-production-key
```

### 2. Update docker-compose.yml for Production
```yaml
services:
  backend:
    build: ./backend
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=${SECRET_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    restart: unless-stopped
    
  frontend:
    build: ./frontend
    restart: unless-stopped
```

### 3. Change Default Ports (if needed)
```yaml
services:
  backend:
    ports:
      - "5000:5000"  # Change from 8000 to 5000
  frontend:
    ports:
      - "3000:80"    # Change from 8080 to 3000
```

### 4. Reverse Proxy (Nginx)
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 5. SSL/HTTPS with Certbot
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```bash
   # Check what's using the ports
   sudo lsof -i :8080
   sudo lsof -i :8000
   
   # Change ports in docker-compose.yml if needed
   ports:
     - "9080:80"  # Frontend on port 9080
     - "9000:5000"  # Backend on port 9000
   ```

2. **Permission Issues**
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER ./backend/uploads ./backend/results
   ```

3. **Container Won't Start**
   ```bash
   # Check container logs
   docker-compose logs backend
   docker-compose logs frontend
   
   # Remove and rebuild
   docker-compose down
   docker-compose build --no-cache
   docker-compose up
   ```

4. **API Connection Issues**
   ```bash
   # Test backend health
   curl http://localhost:8000/api/health
   
   # Check if backend is accessible from frontend container
   docker-compose exec frontend curl http://backend:5000/api/health
   ```

5. **Build Failures**
   ```bash
   # Clean Docker system
   docker system prune -a
   
   # Rebuild with fresh cache
   docker-compose build --no-cache
   ```

### Performance Optimization

1. **Resource Limits**
   ```yaml
   services:
     backend:
       deploy:
         resources:
           limits:
             memory: 1G
             cpus: '0.5'
   ```

2. **Multi-stage Build Optimization**
   - Frontend uses multi-stage build (already implemented)
   - Separate build and runtime environments
   - Minimal production images

### Monitoring

1. **Health Checks**
   ```bash
   # Backend health endpoint
   curl http://localhost:8000/api/health
   
   # Docker health status
   docker-compose ps
   ```

2. **Log Monitoring**
   ```bash
   # Real-time logs
   docker-compose logs -f
   
   # Container stats
   docker stats
   ```

---

## Scaling for Production

### Horizontal Scaling
```yaml
services:
  backend:
    deploy:
      replicas: 3
    depends_on:
      - redis
      
  redis:
    image: redis:alpine
    
  nginx:
    image: nginx:alpine
    depends_on:
      - backend
```

### Load Balancing
Use Nginx or Traefik for load balancing multiple backend containers.

---

## Security Considerations

1. **Change Default Credentials**
2. **Use Strong Secret Keys**
3. **Enable HTTPS in Production**
4. **Implement Rate Limiting**
5. **Regular Security Updates**
6. **File Upload Validation**
7. **Network Segmentation**

---

## Support

For issues:
1. Check container logs: `docker-compose logs`
2. Verify network connectivity
3. Check file permissions
4. Review configuration files
5. Restart services: `docker-compose restart`

**Happy log parsing! 🚀**