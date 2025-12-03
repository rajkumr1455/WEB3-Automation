# Quick Setup Guide: Web3 Bounty Automation Platform

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] **Windows 10/11** (64-bit)
- [ ] **Docker Desktop for Windows** installed and running
- [ ] **Ollama for Windows** installed
- [ ] **NVIDIA RTX 4060** with latest drivers
- [ ] **32GB RAM**
- [ ] **100GB+ free disk space**

## Step-by-Step Setup

### 1. Install Docker Desktop

1. Download Docker Desktop from https://www.docker.com/products/docker-desktop/
2. Install with default settings
3. Enable WSL 2 backend
4. Set resource limits in Settings:
   - CPUs: 8-12
   - Memory: 16-20 GB
   - Swap: 4 GB

### 2. Install Ollama

```powershell
# Download from https://ollama.ai/download/windows
# Or use winget
winget install Ollama.Ollama

# Verify installation
ollama --version

# Pull required models (this will take 30-60 minutes)
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
git clone <your-repo-url> web3_hunter
cd web3_hunter\New

# Create environment file
copy .env.example .env

# Edit .env with your API keys
notepad .env
```

**Required in .env:**
```env
CLAUDE_API_KEY=sk-ant-xxxxx  # Get from https://console.anthropic.com/
```

**Optional in .env:**
```env
GITHUB_TOKEN=ghp_xxxxx
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
ETH_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/...
```

### 4. Verify Ollama Connectivity

```powershell
# Ensure Ollama is running
Start-Process ollama serve

# Test from host
curl http://localhost:11434/api/tags

# Test Docker can reach host (critical!)
docker run --rm curlimages/curl curl http://host.docker.internal:11434/api/tags

# You should see list of models - if not, check Windows Firewall
```

### 5. Build and Start Services

```powershell
# Build all containers (first time only, takes 10-15 minutes)
docker-compose build

# Start all services
docker-compose up -d

# Watch logs
docker-compose logs -f

# Verify all services are running
docker-compose ps
```

### 6. Access the System

Open your browser and navigate to:

- **Web UI**: http://localhost:3001
- **Orchestrator API**: http://localhost:8001
- **Grafana Dashboard**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Qdrant**: http://localhost:6333/dashboard

### 7. Run Your First Scan

**Via Web UI:**
1. Go to http://localhost:3001
2. Fill out the scan form on the dashboard
3. Click "Launch Scan"
4. Monitor progress in real-time

**Via API:**
```powershell
$response = Invoke-RestMethod -Uri "http://localhost:8001/scan" -Method Post -Body (@{
    target_url = "https://github.com/OpenZeppelin/openzeppelin-contracts"
    contract_address = ""
    chain = "ethereum"
} | ConvertTo-Json) -ContentType "application/json"

$scanId = $response.scan_id
Write-Host "Scan started: $scanId"

# Check status
Invoke-RestMethod -Uri "http://localhost:8001/scan/$scanId"
```

## GPU Acceleration Verification

```powershell
# Monitor GPU usage
nvidia-smi -l 1

# When Ollama is processing, you should see:
# - GPU utilization increasing
# - Memory usage on GPU
# DirectML is used automatically on Windows
```

## Troubleshooting

### Ollama Not Accessible from Docker

**Problem**: Containers can't reach Ollama on host

**Solution**:
```powershell
# Check Windows Firewall
New-NetFirewallRule -DisplayName "Ollama" -Direction Inbound -LocalPort 11434 -Protocol TCP -Action Allow

# Verify Ollama is listening
netstat -an | findstr :11434

# Test from container
docker run --rm curlimages/curl curl -v http://host.docker.internal:11434/api/tags
```

### Out of VRAM

**Problem**: "CUDA out of memory" or slow responses

**Solution**:
- Models load sequentially (one at a time)
- Close other GPU applications
- Reduce concurrent scans in settings
- Monitor with: `nvidia-smi`

### Container Build Failures

**Problem**: Docker build errors

**Solution**:
```powershell
# Clear Docker cache
docker system prune -a

# Rebuild specific service
docker-compose build --no-cache <service-name>

# Check Docker Desktop has enough resources allocated
```

### Port Conflicts

**Problem**: Port already in use

**Solution**:
```powershell
# Find what's using the port
netstat -ano | findstr :<port>

# Kill the process
taskkill /PID <process-id> /F

# Or change ports in docker-compose.yml
```

### Web UI Not Loading

**Problem**: Can't access localhost:3001

**Solution**:
- Check if web-ui container is running: `docker ps`
- Check logs: `docker logs web-ui`
- Verify backend is accessible: `curl http://localhost:8001/health`
- Try rebuilding: `docker-compose build web-ui && docker-compose up -d web-ui`

## Performance Optimization

### 1. Disable Windows Defender for Docker Directories

```powershell
# Run as Administrator
Add-MpPreference -ExclusionPath "C:\ProgramData\Docker"
Add-MpPreference -ExclusionPath "$env:USERPROFILE\.docker"
```

### 2. Enable GPU Hardware Scheduling

1. Open Settings → System → Display
2. Graphics Settings → Change default graphics settings
3. Enable "Hardware-accelerated GPU scheduling"
4. Restart

### 3. Use SSD for Docker Data

1. Open Docker Desktop Settings
2. Resources → Advanced
3. Change "Disk image location" to SSD path

## Daily Operations

### Start System
```powershell
# Ensure Ollama is running
Start-Process ollama serve

# Start all Docker services
docker-compose up -d
```

### Stop System
```powershell
# Stop Docker services
docker-compose down

# Ollama will continue running (optional to stop)
```

### Update System
```powershell
# Pull latest code
git pull

# Rebuild changed services
docker-compose build

# Restart
docker-compose down && docker-compose up -d
```

### View Logs
```powershell
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f orchestrator

# Last 100 lines
docker-compose logs --tail=100 llm-router
```

### Clean Up
```powershell
# Remove old scan data
Remove-Item -Recurse -Force data/scans/*

# Remove Docker volumes
docker-compose down -v

# Clean Docker system
docker system prune -a
```

## What's Next?

1. ✅ System is running
2. ✅ First scan completed
3. 📖 Read the documentation in `docs/`
4. 🎯 Configure bug bounty platform integrations
5. 🔧 Customize Semgrep rules in `configs/semgrep/`
6. 📊 Set up Grafana dashboards
7. 🔔 Configure Slack/GitHub notifications
8. 🚀 Start hunting bugs!

## Getting Help

- **Documentation**: Check `docs/` directory
- **Logs**: `docker-compose logs -f`
- **Health**: `docker-compose ps` and Web UI `/agents` page
- **Issues**: Check container logs for errors

Happy bug hunting! 🔒🎯
