# Deployment Guide

This guide covers deploying the Clerc application to both **Vercel** and **EC2** environments with proper backend integration.

## Architecture Overview

The application consists of:
- **Frontend**: Next.js application (this repository)
- **Backend**: Docker-based microservices with nginx proxy
- **Services**: AI, LLM, Document, S3, Company, and Prediction services

## Environment Configuration

### Frontend Environment Variables

The frontend uses different environment files for different deployment scenarios:

#### Development (`.env.development`)
```bash
BACKEND_ORIGIN=http://localhost
```

#### Production (`.env.production`)
```bash
BACKEND_ORIGIN=https://clercbackend.clerc.uk
```

#### EC2 Deployment (`.env.ec2`)
```bash
# Copy to .env.local for EC2 deployment
BACKEND_ORIGIN=https://your-ec2-domain.com
# Or: BACKEND_ORIGIN=http://YOUR_EC2_IP
```

### Backend CORS Configuration

The backend nginx configuration (`backend/nginx/nginx.conf`) supports:
- ✅ `localhost:3000` (development)
- ✅ `*.solaiys-projects.vercel.app` (Vercel deployments)
- ✅ `*.clerc.uk` (production domains)
- ✅ `*.ec2.amazonaws.com` (EC2 domains)
- ✅ `*.compute.amazonaws.com` (EC2 compute domains)

## Deployment Options

## 1. Vercel Deployment

### Prerequisites
- Vercel account
- Backend deployed and accessible at your production domain

### Steps

1. **Connect Repository to Vercel**
   ```bash
   # Install Vercel CLI
   npm i -g vercel

   # Deploy from frontend directory
   cd frontend
   vercel
   ```

2. **Environment Variables**
   In Vercel dashboard, set:
   ```
   BACKEND_ORIGIN=https://clercbackend.clerc.uk
   ```

3. **Custom Domain (Optional)**
   - Add your custom domain in Vercel dashboard
   - Update backend CORS to include your domain

### Automatic Deployment
- Pushes to `main` branch trigger production deployments
- Pull requests create preview deployments with unique URLs

## 2. EC2 Deployment

### Prerequisites
- EC2 instance with Node.js 18+ and Docker
- Domain name or public IP
- SSL certificate (recommended)

### Option A: Traditional Server Deployment

1. **Prepare EC2 Instance**
   ```bash
   # Install Node.js 18+
   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
   sudo apt-get install -y nodejs

   # Install PM2 for process management
   npm install -g pm2
   ```

2. **Deploy Frontend**
   ```bash
   # Clone repository
   git clone <your-repo-url>
   cd Clerc/frontend

   # Create environment file
   cp .env.ec2 .env.local
   # Edit .env.local with your actual backend URL

   # Build and start
   npm install
   npm run build
   pm2 start npm --name "clerc-frontend" -- start
   pm2 save
   pm2 startup
   ```

3. **Deploy Backend**
   ```bash
   cd ../backend
   # Update CORS in nginx.conf if using custom domain
   docker-compose up -d
   ```

### Option B: Static Export for S3/CloudFront

1. **Build Static Export**
   ```bash
   cd frontend
   cp .env.ec2 .env.local
   # Edit .env.local with your backend URL

   # Set static export flag
   echo "STATIC_EXPORT=true" >> .env.local
   echo "EC2_DEPLOYMENT=true" >> .env.local

   npm run build
   ```

2. **Deploy to S3**
   ```bash
   aws s3 sync out/ s3://your-bucket-name --delete
   aws cloudfront create-invalidation --distribution-id YOUR_DISTRIBUTION_ID --paths "/*"
   ```

## 3. Custom Domain Setup

### For EC2
1. **Nginx Configuration**
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;

       location / {
           proxy_pass http://localhost:3000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

2. **SSL with Let's Encrypt**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com
   ```

### For Vercel
1. Add custom domain in Vercel dashboard
2. Update DNS records as instructed
3. SSL is automatic

## API Routing Flow

### Development
```
Frontend (localhost:3000) → Next.js rewrites → Backend (localhost:80)
```

### Production (Vercel)
```
Frontend (yourdomain.com) → Next.js rewrites → Backend (clercbackend.clerc.uk)
```

### Production (EC2)
```
Frontend (yourdomain.com) → Next.js rewrites → Backend (same domain or different)
```

## Environment Variables Reference

| Variable | Purpose | Example |
|----------|---------|---------|
| `BACKEND_ORIGIN` | Backend URL for API rewrites | `https://api.yourdomain.com` |
| `VERCEL` | Auto-set by Vercel | `1` |
| `VERCEL_ENV` | Vercel environment | `production` |
| `EC2_DEPLOYMENT` | Flag for EC2-specific config | `true` |
| `STATIC_EXPORT` | Enable static export | `true` |

## Troubleshooting

### CORS Errors
1. Check backend nginx CORS configuration includes your frontend domain
2. Verify `BACKEND_ORIGIN` environment variable is correct
3. Ensure protocol (http/https) matches between frontend and backend

### API Routes Not Working
1. Verify `BACKEND_ORIGIN` is set correctly
2. Check Next.js rewrite configuration in `next.config.mjs`
3. Test backend directly: `curl https://your-backend.com/health`

### Build Failures
1. Check Node.js version (requires 18+)
2. Clear Next.js cache: `npx next clean`
3. Verify all environment variables are set

### SSL/HTTPS Issues
1. Ensure backend supports HTTPS if frontend is HTTPS
2. Check SSL certificate validity
3. Verify mixed content policies

## Production Checklist

### Frontend
- [ ] Environment variables configured
- [ ] Production build successful (`npm run build`)
- [ ] Custom domain configured (if applicable)
- [ ] SSL certificate active

### Backend
- [ ] All services running (`docker-compose ps`)
- [ ] CORS configured for frontend domain
- [ ] Health checks passing
- [ ] SSL configured for API domain

### DNS
- [ ] A/CNAME records pointing to correct servers
- [ ] SSL certificates valid
- [ ] CDN configured (if using CloudFront/Vercel)

## Monitoring

### Logs
- **Vercel**: Check deployment logs in Vercel dashboard
- **EC2**: Use `pm2 logs` for frontend, `docker-compose logs` for backend

### Health Checks
- Frontend: `https://yourdomain.com`
- Backend: `https://yourbackend.com/health`
- Individual services: `https://yourbackend.com/documents/health`

## Scaling Considerations

### Frontend
- **Vercel**: Automatic scaling
- **EC2**: Use load balancer + multiple instances

### Backend
- Use Docker Swarm or Kubernetes for orchestration
- Implement database replication
- Add Redis for caching
- Use CDN for static assets

## Security Best Practices

1. **Always use HTTPS in production**
2. **Keep dependencies updated**
3. **Use environment variables for secrets**
4. **Implement proper CORS policies**
5. **Use strong SSL certificates**
6. **Enable security headers**
7. **Regular security audits**

## Support

For deployment issues:
1. Check this documentation
2. Verify environment variables
3. Test backend connectivity
4. Check application logs
5. Contact development team with specific error messages