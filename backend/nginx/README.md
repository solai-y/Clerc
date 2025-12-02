# NGINX Reverse Proxy

NGINX configuration for routing and load balancing across all Clerc microservices.

## Overview

The NGINX service acts as a reverse proxy and API gateway for all backend microservices. It provides unified routing, CORS management, request forwarding, and serves as the single entry point for the Clerc backend infrastructure.

## Key Features

- **Reverse Proxy**: Routes requests to appropriate microservices
- **CORS Management**: Configurable cross-origin resource sharing
- **Load Balancing**: Distributes traffic across service instances
- **Large File Support**: Configured for file uploads up to 100MB
- **Service Discovery**: Maps service names to internal Docker network addresses

## Upstream Services

The NGINX configuration proxies the following services:

| Service | Internal Address | Port |
|---------|-----------------|------|
| company-service | company-service:5001 | 5001 |
| document-service | document-service:5002 | 5002 |
| s3-service | s3-service:5003 | 5003 |
| ai-service | ai-service:5004 | 5004 |
| llm-service | llm-service:5005 | 5005 |
| prediction-service | prediction-service:5006 | 5006 |
| tag-service | tag-service:5007 | 5007 |
| text-extraction-service | text-extraction-service:5008 | 5008 |
| retraining-service | retraining-service:5009 | 5009 |
| api-gateway | api-gateway:8000 | 8000 |

## CORS Configuration

The NGINX configuration includes a dynamic CORS allowlist:

**Allowed Origins:**
- `http://localhost:3000` - Local development
- `https://clerc(-git-[branch])-solaiys-projects.vercel.app` - Vercel preview deployments
- `https://clerc.uk` - Production domain
- `https://*.clerc.uk` - Production subdomains
- `https://*.ec2.amazonaws.com` - EC2 domains
- `https://*.compute.amazonaws.com` - EC2 compute domains

**CORS Headers:**
- Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS
- Headers: Content-Type, Authorization, X-Requested-With
- Credentials: Supported

## URL Routing

### API Gateway Documentation
- `/docs` → api-gateway:8000/docs (Unified Swagger UI)
- `/redoc` → api-gateway:8000/redoc (Unified ReDoc)
- `/openapi.json` → api-gateway:8000/openapi.json

### Service Endpoints
- `/company/*` → company-service:5001
- `/documents/*` → document-service:5002
- `/s3/*` → s3-service:5003
- `/ai/*` → ai-service:5004
- `/llm/*` → llm-service:5005
- `/predict/*` → prediction-service:5006
- `/tags/*` → tag-service:5007
- `/extract-text/*` → text-extraction-service:5008
- `/retraining/*` → retraining-service:5009

## Configuration File

**Location:** `/etc/nginx/nginx.conf`

**Key Settings:**
```nginx
client_max_body_size 100m;  # Max upload size
listen 80;                   # HTTP port
```

## Running with Docker

**Standalone:**
```bash
cd backend
docker-compose up -d nginx
```

**With All Services:**
```bash
cd backend
docker-compose up -d
```

The NGINX service automatically depends on all microservices in docker-compose.yml.

## Service Configuration

- **Port:** 80 (HTTP)
- **Image:** nginx:latest
- **Volume:** `./nginx/nginx.conf:/etc/nginx/nginx.conf:ro` (read-only)
- **Dependencies:** All microservices

## Docker Compose Configuration

```yaml
nginx:
  image: nginx:latest
  ports:
    - "80:80"
  volumes:
    - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
  depends_on:
    - company-service
    - document-service
    - s3-service
    # ... all other services
```

## Access Points

Once running, access services via:

- **API Documentation**: `http://localhost/docs`
- **ReDoc**: `http://localhost/redoc`
- **Health Checks**: `http://localhost/[service]/health`
- **Service Endpoints**: `http://localhost/[service]/[endpoint]`

## Testing the Configuration

**Test NGINX configuration syntax:**
```bash
docker exec backend-nginx-1 nginx -t
```

**Reload configuration:**
```bash
docker exec backend-nginx-1 nginx -s reload
```

**View NGINX logs:**
```bash
docker logs backend-nginx-1
```

## Modifying CORS Settings

To add new allowed origins, edit `nginx.conf`:

```nginx
map $http_origin $cors_origin {
    default "";
    "~^https://your-new-domain\.com$"   $http_origin;
}
```

Then reload:
```bash
docker-compose restart nginx
```

## File Upload Configuration

The current configuration supports uploads up to 100MB:

```nginx
client_max_body_size 100m;
```

To increase, modify this value and reload NGINX.

## Troubleshooting

**502 Bad Gateway:**
- Check if backend services are running: `docker-compose ps`
- Verify service health: `curl http://localhost/[service]/health`
- Check NGINX logs: `docker logs backend-nginx-1`

**CORS Errors:**
- Verify origin matches allowlist patterns
- Check browser console for specific CORS error
- Review CORS headers in response

**Connection Timeouts:**
- Increase proxy timeouts in nginx.conf:
  ```nginx
  proxy_connect_timeout 60s;
  proxy_send_timeout 60s;
  proxy_read_timeout 60s;
  ```

## Production Considerations

For production deployment:
1. Enable HTTPS/SSL with Let's Encrypt
2. Add rate limiting
3. Configure caching for static assets
4. Enable gzip compression
5. Add security headers (HSTS, CSP, etc.)
6. Set up log rotation
7. Configure health check monitoring
