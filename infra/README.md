# Docker Infrastructure

Docker Compose configuration cho UIT AI Assistant.

## Structure

```
infra/
├── docker-compose.yml          # Base config (shared)
├── docker-compose.override.yml # Dev overrides (auto-merged)
└── docker-compose.prod.yml     # Prod overrides (explicit)
```

## Services

- **mongodb**: MongoDB database - Port 27018
- **redis**: Redis cache - Port 6380
- **mcp-server**: MCP tools server - Port 8000
- **agent**: LangGraph agent (gRPC) - Port 50051
- **api-gateway**: Go REST API - Port 8080
- **web**: React frontend - Port 3000 (dev) / 80 (prod)

## Architecture

```
Browser :3000
    ↓
web (React)
    ↓ :8080
api-gateway (Go)
    ├─→ MongoDB :27017
    └─→ agent :50051 (gRPC)
           ↓ :8000
        mcp-server (Python)
           ├─→ Redis :6379
           └─→ data/ (RAG documents)
```

## Quick Start

### Development (Local)

Tự động merge `docker-compose.yml` + `docker-compose.override.yml`:

```bash
cd infra

# Start all services
docker compose up

# Start with rebuild
docker compose up --build

# Start in background
docker compose up -d

# View logs
docker compose logs -f

# View specific service logs
docker compose logs -f mcp-server agent

# Restart a service
docker compose restart mcp-server

# Stop all services
docker compose down
```

**Dev URLs:**
- Frontend: http://localhost:3000
- API Gateway: http://localhost:8080
- MCP Server: http://localhost:8000
- MongoDB: localhost:27018
- Redis: localhost:6380

### Production (Server/CI)

Explicitly merge `docker-compose.yml` + `docker-compose.prod.yml`:

```bash
cd infra

# Start all services
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# View logs
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f

# Stop
docker compose -f docker-compose.yml -f docker-compose.prod.yml down
```

**Prod URL:**
- Frontend: http://localhost:80

## Environment Files

### Development
- `apps/mcp-server/.env.dev`
- `apps/agent/.env.dev`
- `apps/api-gateway/.env.dev`

### Production
- `apps/mcp-server/.env.prod`
- `apps/agent/.env.prod`
- `apps/api-gateway/.env.prod`

Tham khảo `.env.example` trong từng folder.

## Data Persistence

- **mongodb_data**: MongoDB data (persisted)
- **../data**: RAG documents (mounted read-only vào mcp-server)

## Troubleshooting

### Service không start được

```bash
# Check logs
docker compose logs [service-name]

# Example
docker compose logs mcp-server
```

### Clear data và restart

```bash
# Stop và xóa volumes
docker compose down -v

# Rebuild và start lại
docker compose up -d --build
```

### Rebuild một service cụ thể

```bash
docker compose up -d --build agent
```

### Access vào container

```bash
docker exec -it uit-ai-agent bash
```

## Docker Compose Override Pattern

**Cách hoạt động:**

1. `docker-compose.yml`: Base configuration (shared settings)
2. `docker-compose.override.yml`: Dev overrides (tự động merge khi dev)
3. `docker-compose.prod.yml`: Prod overrides (phải chỉ định rõ)

**Lợi ích:**
- ✅ DRY: Không lặp code
- ✅ Clear: Base + overrides dễ hiểu
- ✅ Dev-friendly: Chỉ cần `docker compose up`
- ✅ CI/CD-ready: Explicit prod config

## Configuration Differences

### Development
- **Volume mounts**: Code hot-reload
- **Build mode**: Development images
- **Commands**: `go run`, `pnpm dev`
- **Logging**: MongoDB logs tắt

### Production
- **No volumes**: Code baked vào images
- **Build mode**: Production images (optimized)
- **Commands**: Compiled binaries
- **Restart policy**: `unless-stopped`
- **Ports**: Web trên port 80

## Next Steps

- [ ] Setup CI/CD với GitHub Actions
- [ ] Configure production secrets
- [ ] Setup monitoring (Prometheus/Grafana)
- [ ] Configure reverse proxy (Traefik/Nginx)
