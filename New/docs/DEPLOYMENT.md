# Production Deployment Guide

## Prerequisites Checklist

Before deploying to production, ensure you have:

- [  ] **Server with minimum specs:**
  - Windows Server 2019/2022 or Windows 10/11 Pro
  - NVIDIA GPU with 8GB+ VRAM (RTX 4060 or better)
  - 32GB RAM
  - 200GB+ SSD storage
  - Static IP or domain name

- [ ] **Software installed:**
  - Docker Desktop for Windows
  - Ollama for Windows
  - Git for Windows

- [ ] **API Keys obtained:**
  - Claude API key from Anthropic
  - (Optional) Etherscan API key
  - (Optional) Slack webhook URL
  - (Optional) GitHub personal access token

- [ ] **Network configuration:**
  - Ports 3001 (Web UI), 8001 (API) exposed
  - Firewall rules configured
  - SSL certificate obtained (if using HTTPS)

---

## Installation Steps

### 1. Install Docker Desktop

```powershell
# Download from https://www.docker.com/products/docker-desktop/
# Install with WSL 2 backend

# Configure resources:
# Settings → Resources → Advanced:
#   CPUs: 12
#   Memory: 20 GB
#   Swap: 4 GB
```

### 2. Install Ollama

```powershell
# Download from https://ollama.ai/download/windows
winget install Ollama.Ollama

# Verify installation
ollama --version

# Pull required models (takes 30-60 minutes)
ollama pull deepseek-r1:32b-q4_K_M
ollama pull qwen2.5:14b-instruct-q4_K_M
ollama pull mistral:7b-instruct-q4_K_M
ollama pull nomic-embed-text

# Verify models
ollama list
```

### 3. Clone and Configure

```powershell
# Clone repository
git clone <your-repo-url> web3-bounty-hunter
cd web3-bounty-hunter

# Create environment file
copy .env.example .env

# Edit .env with production values
notepad .env
```

**Critical .env variables:**
```env
# Required
CLAUDE_API_KEY=sk-ant-xxxxx

# Recommended
ETH_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK
GITHUB_TOKEN=ghp_xxxxx

# Optional
GRAFANA_PASSWORD=<strong-password>
IMMUNEFI_API_KEY=xxxxx
HACKENPROOF_API_KEY=xxxxx
```

### 4. Windows Firewall Configuration

```powershell
# Run as Administrator
# Allow Ollama
New-NetFirewallRule -DisplayName "Ollama" -Direction Inbound -LocalPort 11434 -Protocol TCP -Action Allow

# Allow Web UI
New-NetFirewallRule -DisplayName "Web3 Hunter UI" -Direction Inbound -LocalPort 3001 -Protocol TCP -Action Allow

# Allow API
New-NetFirewallRule -DisplayName "Web3 Hunter API" -Direction Inbound -LocalPort 8001 -Protocol TCP -Action Allow
```

### 5. Build and Deploy

```powershell
# Build all containers
docker-compose build

# Start all services
docker-compose up -d

# Verify all services are running
docker-compose ps

# Check logs
docker-compose logs -f
```

### 6. Populate Knowledge Base (Optional but Recommended)

```powershell
# Install Python dependencies
pip install httpx web3

# Populate RAG
python scripts/populate_rag.py
```

### 7. Run System Tests

```powershell
# Test all components
python scripts/test_e2e.py
```

---

## Production Hardening

### 1. Enable HTTPS (Recommended)

Add reverse proxy with Nginx:

```yaml
# docker-compose.override.yml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - web-ui
      - orchestrator
```

**nginx.conf example:**
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    location / {
        proxy_pass http://web-ui:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api/ {
        proxy_pass http://orchestrator:8001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 2. Add Authentication

Create `docker-compose.override.yml`:

```yaml
services:
  web-ui:
    environment:
      - NEXTAUTH_URL=https://your-domain.com
      - NEXTAUTH_SECRET=<generate-strong-secret>
```

### 3. Database for Scan State

Replace in-memory storage with Redis:

```yaml
services:
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - web3-net

volumes:
  redis-data:
```

### 4. Automated Backups

```powershell
# backup.ps1
$timestamp = Get-Date -Format "yyyy-MM-dd-HHmmss"
$backupDir = "backups/$timestamp"

# Create backup directory
New-Item -ItemType Directory -Force -Path $backupDir

# Backup volumes
docker run --rm -v qdrant-data:/data -v ${PWD}/backups:/backup alpine tar czf /backup/${timestamp}/qdrant-data.tar.gz -C /data .
docker run --rm -v prometheus-data:/data -v ${PWD}/backups:/backup alpine tar czf /backup/${timestamp}/prometheus-data.tar.gz -C /data .
docker run --rm -v grafana-data:/data -v ${PWD}/backups:/backup alpine tar czf /backup/${timestamp}/grafana-data.tar.gz -C /data .

# Backup .env
Copy-Item .env $backupDir/.env

Write-Host "Backup complete: $backupDir"
```

**Add to Task Scheduler for daily backups.**

### 5. Monitoring and Alerts

Configure Grafana alerts:

1. Open http://localhost:3000
2. Go to Alerting → Alert rules
3. Create alerts for:
   - High error rate
   - Service down
   - High memory usage
   - Long scan times

### 6. Resource Limits

```yaml
# docker-compose.override.yml
services:
  static-agent:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
  
  fuzzing-agent:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

---

## Maintenance

### Daily Tasks

```powershell
# Check service health
docker-compose ps

# Check logs for errors
docker-compose logs --tail=100 orchestrator
```

### Weekly Tasks

```powershell
# Update Ollama models
ollama pull deepseek-r1:32b-q4_K_M
ollama pull qwen2.5:14b-instruct-q4_K_M
ollama pull mistral:7b-instruct-q4_K_M

# Clean up old scans (if using in-memory storage)
# Manual cleanup or implement retention policy
```

### Monthly Tasks

```powershell
# Update Docker images
docker-compose pull
docker-compose up -d

# Review and rotate logs
docker system prune -a

# Update knowledge base
python scripts/populate_rag.py
```

---

## Troubleshooting

### Services Won't Start

```powershell
# Check Docker Desktop
docker info

# Check logs
docker-compose logs <service-name>

# Rebuild specific service
docker-compose build --no-cache <service-name>
docker-compose up -d <service-name>
```

### Ollama Not Accessible

```powershell
# Verify Ollama is running
Get-Process ollama

# Test from host
curl http://localhost:11434/api/tags

# Test from container
docker run --rm curlimages/curl curl http://host.docker.internal:11434/api/tags
```

### Out of Memory

```powershell
# Check Docker resource usage
docker stats

# Increase Docker memory limit
# Docker Desktop → Settings → Resources

# Reduce concurrent scans
# Edit .env: MAX_CONCURRENT_SCANS=2
```

### SSL Certificate Issues

```powershell
# Generate self-signed cert for testing
openssl req -x509 -nodes -days 365 -newkey rsa:2048 `
  -keyout ssl/key.pem -out ssl/cert.pem
```

---

## Performance Tuning

### GPU Optimization

```powershell
# Enable hardware-accelerated GPU scheduling
# Settings → System → Display → Graphics settings

# Monitor GPU usage
nvidia-smi -l 1
```

### Disk I/O

```powershell
# Move Docker data to SSD
# Docker Desktop → Settings → Resources → Disk image location
```

### Network

```powershell
# Use localhost for inter-service communication
# Services should use service names (e.g., http://llm-router:8000)
# not http://localhost:8000
```

---

## Scaling

### Horizontal Scaling (Multiple Instances)

For high load, deploy multiple instances behind a load balancer:

```
          Load Balancer (Nginx)
         /         |         \
    Instance 1  Instance 2  Instance 3
```

Each instance should:
- Use shared Redis for scan state
- Use shared Qdrant for knowledge base
- Have unique Ollama instance (local)
- Share Claude API quota

### Vertical Scaling (More Resources)

For single instance:
- Increase Docker memory to 24-28 GB
- Allocate 10-14 CPU cores
- Use NVMe SSD for volumes

---

## Security Checklist

- [ ] HTTPS enabled with valid certificate
- [ ] Authentication enabled (JWT or OAuth)
- [ ] API rate limiting configured
- [ ] Strong passwords for Grafana, databases
- [ ] Environment variables secured (not committed to git)
- [ ] Firewall rules minimized
- [ ] Regular security updates
- [ ] Audit logs enabled
- [ ] Sensitive logs redacted
- [ ] Backup encryption enabled

---

## Support

For issues:
1. Check logs: `docker-compose logs -f`
2. Review STATUS.md for known issues
3. Check GitHub issues
4. Contact support

**Happy hunting! 🔒🎯**
