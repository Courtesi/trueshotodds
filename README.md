# TrueShot Odds

Sports arbitrage betting platform that identifies and analyzes arbitrage opportunities across multiple sportsbooks in real-time.

## Project Structure

This is a monorepo using Git submodules to manage three separate services:

```
trueshotodds_v2/
  backend/          # FastAPI backend service
  webscraper/       # Arbitrage detection worker
  frontend/         # React frontend application
  docker-compose.yml
```

Each service is maintained in its own Git repository as a submodule.

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- uv package manager (for local development)
- Node.js 18+ (for frontend development)
- Redis (runs via Docker Compose)

### Installation

1. **Clone with submodules**:
   ```bash
   git clone --recurse-submodules https://github.com/Courtesi/trueshotodds_v2.git
   cd trueshotodds_v2
   ```

   Or if already cloned:
   ```bash
   git submodule init
   git submodule update
   ```

2. **Set up environment files**:
   ```bash
   # Backend
   cp backend/.env.example backend/.env
   # Edit backend/.env with your credentials
   # Firebase service account details below

   # Webscraper
   cp webscraper/.env.example webscraper/.env
   # Edit webscraper/.env with your configuration

   # Frontend (In prod, should move .env variables in frontend/ to root because variables need to be available at buildtime, not just runtime)
   cp frontend/.env.example frontend/.env
   # Edit frontend/.env with your configuration
   ```

3. **Add Firebase credentials**:
   ```bash
   # Place your Firebase service account JSON
   cp /path/to/service-account.json backend/service-account.json
   ```

### Running with Docker

**Production mode**:
```bash
docker compose up
```

This starts:
- **Redis** on port 6379
- **Backend** (FastAPI) - internal only
- **Webscraper** - background worker
- **Frontend** on port 5173

**Development mode** (individual services):
```bash
# Backend only
docker compose up backend redis

# Webscraper only
docker compose up webscraper redis

# Frontend only
docker compose up frontend
```

### Running Locally (Development)

**Backend**:
```bash
cd backend
uv sync
uv run fastapi dev
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

**Webscraper**:
```bash
cd webscraper
uv sync
uv run python main.py
```

**Frontend**:
```bash
cd frontend
npm install
npm run dev
# App: http://localhost:5173
```

## Services Overview

### Backend (FastAPI)
- RESTful API for arbitrage data
- User authentication & subscription management
- Redis caching layer
- Stripe payment integration
- Firebase authentication

**Tech**: Python 3.11, FastAPI, Redis, Firebase, Stripe

[Backend Documentation](https://github.com/Courtesi/tso_backend/blob/09c415410a05298aa6d78a7d111e4961792cc0cc/README.md)

### Webscraper
- Real-time arbitrage detection across multiple sportsbooks
- Parallel market fetching with ThreadPoolExecutor
- Mock mode for development/testing
- Publishes opportunities to Redis

**Tech**: Python 3.11, Redis, Multi-threaded scraping

[Webscraper Documentation](https://github.com/Courtesi/tso_webscraper/blob/eab5d3a79b46012a3c95ac87b673bb275a329982/README.md)

### Frontend
- Modern React-based UI
- Real-time arbitrage opportunity display
- User authentication & subscriptions
- Responsive design

**Tech**: React, Vite, TypeScript

[Frontend Documentation](https://github.com/Courtesi/tso_frontend/blob/cb9fa5ee9fcc2021396e57a19d363c289291ff88/README.md)

## Architecture

```
   +-------------+
   |  Frontend   |  (React, Port 5173)
   +------+------+
          | HTTP
          v
   +-------------+      +--------------+
   |   Backend   |<---->|    Redis     |
   |  (FastAPI)  |      |   (Cache)    |
   +------+------+      +------^-------+
          |                    |
          | Firebase           | Pub/Sub
          | Stripe             |
          v                    |
   +-------------+      +------+-------+
   |  External   |      |  Webscraper  |
   |  Services   |      |   (Worker)   |
   +-------------+      +------+-------+
                               |
                               v
                        +--------------+
                        |  Sportsbooks |
                        |     APIs     |
                        +--------------+
```

## Development Workflow

### Working on Submodules

Each submodule is an independent Git repository. When you make changes:

```bash
# 1. Make changes in a submodule
cd backend
git add .
git commit -m "your changes"
git push origin main

# 2. Update the root repository to point to new commit
cd ..
git add backend
git commit -m "chore: update backend submodule"
git push origin main
```

### Updating Submodules to Latest

```bash
# Update all submodules to their latest commits
git submodule update --remote --merge

# Commit the updates
git add .
git commit -m "chore: update all submodules to latest"
git push
```

```bash
# Sync changes (overwriting your own) to the latest commits
git pull --recurse-submodules
```

### Pre-commit Hooks

Both backend and webscraper use pre-commit hooks for:
- **Ruff linting** - Automatic code quality checks
- **README auto-sync** - Keep documentation in sync with `.env.example` files

Set up hooks in each submodule:
```bash
cd backend
uv run pre-commit install

cd webscraper
uv run pre-commit install
```

## Environment Variables

### Backend (`backend/secrets/.env`)
- Firebase credentials
- Stripe API keys
- Redis connection
- Email service (Resend)

### Webscraper (`webscraper/.env`)
- Mock mode toggle
- Redis connection
- Cache TTL settings
- Generation intervals

### Frontend (`frontend/.env`)
- API URL
- Firebase config
- Stripe publishable key

See individual service README files for detailed configuration.

## Deployment

### Docker Compose (Production)

```bash
# Build and start all services
docker compose up --build -d

# View logs
docker compose logs -f

# Stop all services
docker compose down
```

### Health Checks

- Backend: `http://localhost:8000/api/health`
- Redis: Automatic health checks in docker compose

## Contributing

1. Work in the appropriate submodule directory
2. Follow the pre-commit hook guidelines
3. Test locally before pushing
4. Update root repository after pushing submodule changes
5. Keep `.env.example` files up to date

## Troubleshooting

### Submodules not initialized
```bash
git submodule init
git submodule update
```

### Docker services not starting
```bash
# Check logs
docker compose logs <service-name>

# Rebuild containers
docker compose down
docker compose up --build
```

### Redis connection issues
```bash
# Ensure Redis is running
docker compose up redis

# Check Redis health
docker exec tso-redis redis-cli ping
```

## Documentation

- [Backend API Documentation](https://github.com/Courtesi/tso_backend/blob/09c415410a05298aa6d78a7d111e4961792cc0cc/README.md)
- [Webscraper Documentation](https://github.com/Courtesi/tso_webscraper/blob/eab5d3a79b46012a3c95ac87b673bb275a329982/README.md)
- [Frontend Documentation](https://github.com/Courtesi/tso_frontend/blob/cb9fa5ee9fcc2021396e57a19d363c289291ff88/README.md)

## License

[Add your license here]

## Support

[Add support information here]