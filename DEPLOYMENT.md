# Clerc Deployment Guide

This guide provides step-by-step instructions for deploying the Clerc document tagging system.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Backend Deployment](#backend-deployment)
- [Frontend Deployment](#frontend-deployment)
- [Production Configuration](#production-configuration)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before deploying Clerc, ensure you have:

- Docker and Docker Compose installed
- Node.js 18+ and npm installed
- Access to AWS account (for S3 and Bedrock)
- Supabase project created
- EC2 instance (for production deployment)

## Environment Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/Clerc.git
cd Clerc
```

### 2. Configure Backend Environment Variables

Create a `.env` file in the `backend/` directory using `.env.example` as a template:

```bash
cd backend
cp .env.example .env
```

Edit `.env` and fill in the following values:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# AWS Configuration (Primary - for S3)
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-s3-bucket-name

# AWS Configuration (Secondary - for Bedrock/Claude)
AWS_ACCESS_KEY_ID2=your-aws-access-key-id-for-bedrock
AWS_SECRET_ACCESS_KEY2=your-aws-secret-access-key-for-bedrock
AWS_REGION2=us-east-1

# Claude Model Configuration
CLAUDE_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0

# Service Configuration
MAX_RETRIES=5
RETRY_DELAY_SECONDS=10
REQUEST_TIMEOUT_SECONDS=30
```

### 3. Configure Frontend Environment Variables

Create a `.env` file in the `frontend/` directory:

```bash
cd ../frontend
cp .env.example .env
```

For local development:

```bash
BACKEND_ORIGIN=http://localhost
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
```

For production, create `.env.production`:

```bash
BACKEND_ORIGIN=https://your-backend-domain.com
```

## Backend Deployment

### Local Development

1. Navigate to the backend directory:

```bash
cd backend
```

2. Start all services with Docker Compose:

```bash
docker compose up --build
```

This will start all microservices:
- Company Service (port 5001)
- Document Service (port 5002)
- S3 Service (port 5003)
- AI Service (port 5004)
- LLM Service (port 5005)
- Prediction Service (port 5006)
- Tag Service (port 5007)
- Text Extraction Service (port 5008)
- Retraining Service (port 5009)
- API Gateway (port 8000)
- Nginx (port 80)

3. Verify services are running:

```bash
docker compose ps
```

### Production Deployment (EC2)

The CI/CD pipeline automatically deploys to EC2 when changes are pushed to the `main` branch.

Manual deployment steps:

1. SSH into your EC2 instance:

```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

2. Navigate to the deployment directory:

```bash
cd /path/to/Clerc/backend
```

3. Pull latest changes:

```bash
git pull origin main
```

4. Rebuild and restart services:

```bash
docker compose down
docker compose up --build -d
```

5. Check service health:

```bash
docker compose logs -f
```

## Frontend Deployment

### Local Development

1. Navigate to the frontend directory:

```bash
cd frontend
```

2. Install dependencies:

```bash
npm install
```

3. Start the development server:

```bash
npm run dev
```

The application will be available at http://localhost:3000

### Production Deployment

1. Build the production bundle:

```bash
npm run build
```

2. Start the production server:

```bash
npm start
```

For deployment to Vercel or similar platforms, connect your repository and configure the following:

- **Framework Preset**: Next.js
- **Build Command**: `npm run build`
- **Output Directory**: `.next`
- **Environment Variables**: Add production variables from `.env.production`

## Production Configuration

### Database Setup (Supabase)

1. Create the following tables in your Supabase project:
   - `companies`
   - `documents`
   - `tags`
   - `training_data`

2. Run the SQL schema from `backend/retraining-service/schema.sql`

3. Set up Row Level Security (RLS) policies as needed

### AWS Configuration

#### S3 Bucket Setup

1. Create an S3 bucket for document storage
2. Configure CORS policy:

```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
        "AllowedOrigins": ["*"],
        "ExposeHeaders": []
    }
]
```

3. Create IAM user with S3 permissions and save credentials

#### AWS Bedrock Setup

1. Enable AWS Bedrock in your region
2. Request access to Claude models
3. Create IAM user with Bedrock permissions
4. Save credentials for LLM service

### Nginx Configuration

The included nginx configuration (`backend/nginx/nginx.conf`) provides:
- Reverse proxy for all backend services
- Load balancing
- Request routing

Modify as needed for your domain and SSL certificates.

## CI/CD Pipeline

The project includes GitHub Actions workflows for:

- **CI (dev)**: `.github/workflows/ci-dev.yml`
  - Runs tests on PRs to `dev` branch
  - Builds Docker images
  - Validates code quality

- **CI/CD (main)**: `.github/workflows/ci-main.yml`
  - Runs tests on PRs to `main` branch
  - Builds and deploys to EC2 on merge
  - Uses rsync for deployment

### GitHub Secrets Required

Configure these secrets in your GitHub repository:

- `EC2_HOST`: EC2 instance IP or hostname
- `EC2_SSH_KEY`: Private SSH key for EC2 access
- `EC2_USER`: SSH username (usually `ubuntu`)

## Health Checks

Verify deployment health by checking these endpoints:

- Document Service: `http://your-domain/documents/health`
- Tag Service: `http://your-domain/tags`
- AI Service: `http://your-domain/ai-service/health`
- Retraining Service: `http://your-domain/retraining/health`

## Troubleshooting

### Services Not Starting

1. Check Docker logs:
```bash
docker compose logs [service-name]
```

2. Verify environment variables are set correctly

3. Ensure all required ports are available

### Database Connection Issues

1. Verify Supabase credentials in `.env`
2. Check Supabase project is active
3. Verify network connectivity to Supabase

### AWS Connection Issues

1. Verify AWS credentials are correct
2. Check IAM permissions for S3 and Bedrock
3. Ensure AWS region is correctly configured

### Frontend Can't Connect to Backend

1. Verify `BACKEND_ORIGIN` is set correctly
2. Check CORS configuration in backend services
3. Verify nginx is running and routing correctly

## Monitoring and Logs

### View Service Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f [service-name]
```

### Check Service Status

```bash
docker compose ps
```

### Restart a Service

```bash
docker compose restart [service-name]
```

## Scaling Considerations

For production deployments:

1. Use a managed database instead of Supabase for better performance
2. Implement Redis for caching
3. Use a CDN for frontend assets
4. Set up load balancing for backend services
5. Implement monitoring with CloudWatch or similar
6. Set up automated backups for S3 and database

## Security Recommendations

1. Never commit `.env` files to version control
2. Rotate AWS and Supabase credentials regularly
3. Implement rate limiting on API endpoints
4. Use HTTPS in production
5. Set up firewall rules to restrict access to backend services
6. Enable AWS CloudTrail for audit logging
7. Implement proper RLS policies in Supabase

## Support

For issues or questions:
- Check the [README.md](README.md) for general information
- Review logs for error messages
- Consult the [API Documentation](docs/API.md)
