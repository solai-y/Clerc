# Clerc

**AI-Powered Document Tagging and Classification System**

Automatically classify, tag, and manage documents using advanced AI models with a modern Next.js frontend and microservices backend.

## Overview

Clerc is an intelligent document tagging system that leverages AI and LLM technology to automatically classify and tag documents. It features a microservice-based architecture with a Next.js frontend, supporting robust document management, automated tagging, and model retraining workflows.

## Features

- **AI-Powered Classification**: Automatic document tagging using machine learning models
- **LLM Integration**: Claude AI integration for intelligent document analysis
- **Document Management**: Upload, view, and manage documents with S3 storage
- **Tag Hierarchy**: Hierarchical tag structure for complex classification
- **Model Retraining**: Continuous model improvement with retraining capabilities
- **Metrics & Analytics**: Track document processing and tagging metrics
- **Modern UI**: Intuitive Next.js frontend with real-time updates
- **Microservices Architecture**: Scalable backend with Docker support
- **CI/CD Pipeline**: Automated testing and deployment with GitHub Actions

## Architecture

```
Clerc/
├── frontend/                    # Next.js application
├── backend/
│   ├── ai-service/             # AI model prediction service
│   ├── api-gateway/            # API gateway and routing
│   ├── company-service/        # Company management service
│   ├── document-service/       # Document CRUD operations
│   ├── llm-service/            # Claude LLM integration
│   ├── prediction-service/     # Prediction orchestration
│   ├── retraining-service/     # Model retraining workflows
│   ├── s3-service/             # AWS S3 file storage
│   ├── tag-service/            # Tag management and hierarchy
│   ├── text-extraction-service/ # PDF text extraction
│   └── nginx/                  # Reverse proxy and load balancing
├── docs/                       # Documentation
├── tests/                      # Test files
└── .github/workflows/          # CI/CD pipelines
```

### Technology Stack

- **Frontend**: Next.js 14, React, TypeScript, Tailwind CSS
- **Backend**: Python Flask microservices, Docker
- **AI/ML**: Custom ML models, AWS Bedrock (Claude)
- **Database**: Supabase (PostgreSQL)
- **Storage**: AWS S3
- **Infrastructure**: Docker Compose, Nginx
- **CI/CD**: GitHub Actions

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ and npm
- AWS account (for S3 and Bedrock)
- Supabase project

### Quick Start

#### 1. Clone the Repository

```bash
git clone https://github.com/your-org/Clerc.git
cd Clerc
```

#### 2. Set Up Backend

```bash
cd backend
cp .env.example .env
# Edit .env with your configuration (Supabase, AWS credentials)
docker compose up --build
```

Backend services will be available at:
- API Gateway: `http://localhost:8000`
- Individual services: ports 5001-5009
- Nginx: `http://localhost:80`

#### 3. Set Up Frontend

```bash
cd frontend
cp .env.example .env
# Edit .env with your configuration
npm install
npm run dev
```

Frontend will be available at: `http://localhost:3000`

## Development

### Environment Variables

Secrets and API keys are managed via `.env` files (not committed to git).

**Backend** (`backend/.env`):
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Supabase anonymous key
- `AWS_ACCESS_KEY_ID`: AWS credentials for S3
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `AWS_ACCESS_KEY_ID2`: AWS credentials for Bedrock
- `AWS_SECRET_ACCESS_KEY2`: Bedrock secret key
- `CLAUDE_MODEL_ID`: Claude model identifier

**Frontend** (`frontend/.env`):
- `BACKEND_ORIGIN`: Backend URL for server-side requests
- `NEXT_PUBLIC_SUPABASE_URL`: Supabase URL (public)
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`: Supabase key (public)

See `.env.example` files for full configuration options.

### Microservices

Each backend service has its own directory, dependencies, and tests:

| Service | Port | Description |
|---------|------|-------------|
| company-service | 5001 | Company data management |
| document-service | 5002 | Document CRUD operations |
| s3-service | 5003 | S3 file storage operations |
| ai-service | 5004 | AI model predictions |
| llm-service | 5005 | Claude LLM integration |
| prediction-service | 5006 | Prediction orchestration |
| tag-service | 5007 | Tag management |
| text-extraction-service | 5008 | PDF text extraction |
| retraining-service | 5009 | Model retraining |
| api-gateway | 8000 | API routing |
| nginx | 80 | Reverse proxy |

## Testing

### Backend Tests

Each microservice contains unit and integration tests using `pytest`:

```bash
# Run tests for a specific service
cd backend/document-service
pytest tests/

# Run with coverage
pytest --cov=. tests/

# Run integration tests (ensure containers are running)
pytest tests/integration/
```

### Frontend Tests

```bash
cd frontend
npm test
```

### End-to-End Tests

```bash
# Ensure all services are running
cd backend
docker compose up -d

# Run E2E tests
pytest tests/e2e/
```

## CI/CD

GitHub Actions are used for continuous integration and deployment:

- **CI (dev)**: On PRs to `dev` branch
  - Builds Docker images
  - Runs backend and frontend tests
  - Validates code quality

- **CI/CD (main)**: On PRs and merges to `main` branch
  - Runs full test suite
  - Deploys to EC2 instance via rsync
  - Updates production environment

### Required GitHub Secrets

- `EC2_HOST`: EC2 instance IP/hostname
- `EC2_SSH_KEY`: SSH private key for EC2
- `EC2_USER`: SSH username

## Documentation

- [DEPLOYMENT.md](DEPLOYMENT.md) - Detailed deployment guide
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [docs/API.md](docs/API.md) - API documentation
- [docs/](docs/) - Additional technical documentation

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:

- Development workflow
- Coding standards
- Testing requirements
- Pull request process

### Quick Contribution Guide

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes and add tests
4. Commit: `git commit -am 'Add: your feature'`
5. Push: `git push origin feature/your-feature`
6. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues, questions, or feature requests:
- Open an issue on GitHub
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for troubleshooting
- Review the [documentation](docs/)

## Acknowledgements

- [Supabase](https://supabase.com/) - Database and authentication
- [AWS](https://aws.amazon.com/) - S3 storage and Bedrock AI
- [Anthropic](https://www.anthropic.com/) - Claude AI models
- [Flask](https://flask.palletsprojects.com/) - Backend framework
- [Next.js](https://nextjs.org/) - Frontend framework

---

Built with ❤️ for intelligent document management
