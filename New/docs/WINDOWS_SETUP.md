# Web3 Bug Bounty Automation System - Windows Setup Guide

This guide will help you set up the complete Web3 Bug Bounty Automation System on Windows 10/11.

## Prerequisites

- Windows 10/11 (64-bit)
- NVIDIA RTX 4060 GPU (8GB VRAM)
- 32GB RAM
- 100GB+ free disk space
- Administrator access

## Step 1: Install Docker Desktop

1. Download Docker Desktop for Windows from https://www.docker.com/products/docker-desktop/
2. Run the installer and follow the prompts
3. Enable WSL 2 backend when prompted
4. Restart your computer
5. Launch Docker Desktop and verify it's running

```powershell
docker --version
docker-compose --version
```

## Step 2: Install Ollama for Windows

### Download and Install

1. Visit https://ollama.ai/download/windows
2. Download the Ollama installer for Windows
3. Run the installer (OllamaSetup.exe)
4. Ollama will install to `C:\Users\<YourUsername>\AppData\Local\Programs\Ollama`

### Enable GPU Acceleration

Ollama on Windows automatically uses DirectML for GPU acceleration with your RTX 4060.

Verify GPU is being used:
```powershell
# Check if Ollama is running
ollama list

# Monitor GPU usage
nvidia-smi
```

### Download Required Models

Open PowerShell and run:

```powershell
# Deep reasoning model (32B quantized - ~20GB)
ollama pull deepseek-r1:32b-q4_K_M

# Code analysis model (14B quantized - ~9GB)
ollama pull qwen2.5:14b-instruct-q4_K_M

# Fast triage model (7B quantized - ~4GB)
ollama pull mistral:7b-instruct-q4_K_M

# Embedding model (~1GB)
ollama pull nomic-embed-text
```

**Note:** These downloads will take 30-60 minutes depending on your internet speed.

### Verify Ollama is Running

```powershell
# Check Ollama service
ollama serve

# In another terminal, test a model
ollama run mistral:7b-instruct-q4_K_M "Hello, test"
```

Ollama should be accessible at `http://localhost:11434`

## Step 3: Clone the Repository

```powershell
cd C:\Users\<YourUsername>\Desktop
git clone <your-repo-url> web3_hunter
cd web3_hunter\New
```

## Step 4: Configure Environment Variables

1. Copy the example environment file:
```powershell
copy .env.example .env
```

2. Edit `.env` with your favorite text editor (Notepad++, VS Code, etc.):

```env
# Required: Claude API Key (get from https://console.anthropic.com/)
CLAUDE_API_KEY=sk-ant-xxxxxxxxxxxxx

# Optional: GitHub Integration
GITHUB_TOKEN=ghp_xxxxxxxxxxxxx
GITHUB_REPO=your-org/private-bounty-repo

# Optional: Slack Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Optional: Email Notifications
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# RPC Endpoints (use your own or keep defaults)
ETH_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY
BSC_RPC_URL=https://bsc-dataseed.binance.org/
POLYGON_RPC_URL=https://polygon-rpc.com/
ARBITRUM_RPC_URL=https://arb1.arbitrum.io/rpc
```

## Step 5: Verify Ollama Connectivity from Docker

Docker containers will access Ollama using `host.docker.internal:11434`.

Test connectivity:
```powershell
docker run --rm curlimages/curl:latest curl -v http://host.docker.internal:11434/api/tags
```

You should see a JSON response with available models.

## Step 6: Build and Start the System

```powershell
# Build all containers (first time only, takes 10-20 minutes)
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

## Step 7: Verify Services are Running

Check all services are healthy:
```powershell
docker-compose ps
```

All services should show "Up" status.

### Access Service Endpoints

- **Orchestrator:** http://localhost:8001
- **LLM Router:** http://localhost:8000
- **Recon Agent:** http://localhost:8002
- **Static Agent:** http://localhost:8003
- **Fuzzing Agent:** http://localhost:8004
- **Monitoring Agent:** http://localhost:8005
- **Triage Agent:** http://localhost:8006
- **Reporting Agent:** http://localhost:8007
- **Qdrant:** http://localhost:6333
- **Prometheus:** http://localhost:9090
- **Grafana:** http://localhost:3000 (admin/admin)

### Health Checks

```powershell
# Check LLM Router
curl http://localhost:8000/health

# Check Orchestrator
curl http://localhost:8001/health

# Check Ollama connectivity
curl http://localhost:8000/models
```

## Step 8: Run Your First Scan

```powershell
# Using PowerShell
$body = @{
    target_url = "https://github.com/your-org/your-contract-repo"
    contract_address = "0x1234567890123456789012345678901234567890"
    chain = "ethereum"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8001/scan" -Method Post -Body $body -ContentType "application/json"
```

You'll receive a `scan_id`. Check progress:
```powershell
curl http://localhost:8001/scan/<scan_id>
```

## Troubleshooting

### Ollama Not Accessible from Docker

1. Ensure Ollama is running: `ollama serve`
2. Test from host: `curl http://localhost:11434/api/tags`
3. Test from Docker: `docker run --rm curlimages/curl curl http://host.docker.internal:11434/api/tags`

### GPU Not Being Used

1. Check NVIDIA drivers are up to date
2. Verify GPU is detected: `nvidia-smi`
3. Ollama on Windows uses DirectML automatically - no additional configuration needed

### Out of VRAM Errors

The system loads models sequentially to stay within 8GB VRAM:
- Only one large model is loaded at a time
- Models are automatically unloaded after use
- If you still see issues, reduce concurrent scans

### Docker Containers Can't Start

1. Ensure Docker Desktop is running
2. Check Docker has enough resources allocated:
   - Settings → Resources → Advanced
   - Recommended: 16GB RAM, 4 CPUs
3. Restart Docker Desktop

### Slow Performance

1. Ensure SSD is being used (not HDD)
2. Close other GPU-intensive applications
3. Monitor GPU usage: `nvidia-smi -l 1`
4. Check Docker resource allocation

## Monitoring

### View Grafana Dashboard

1. Open http://localhost:3000
2. Login: admin/admin (change password on first login)
3. Navigate to Dashboards → Web3 Bounty Automation System

### View Prometheus Metrics

1. Open http://localhost:9090
2. Query examples:
   - `orchestrator_active_scans` - Current active scans
   - `rate(llm_router_requests_total[5m])` - LLM request rate
   - `orchestrator_scan_duration_seconds` - Scan duration

## Updating the System

```powershell
# Pull latest code
git pull

# Rebuild containers
docker-compose build

# Restart services
docker-compose down
docker-compose up -d
```

## Stopping the System

```powershell
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes all data)
docker-compose down -v
```

## Performance Optimization

### Windows-Specific Optimizations

1. **Disable Windows Defender real-time scanning for Docker directories:**
   - Settings → Windows Security → Virus & threat protection
   - Add exclusions for Docker Desktop data directory

2. **Enable Hardware-accelerated GPU scheduling:**
   - Settings → Display → Graphics settings
   - Enable "Hardware-accelerated GPU scheduling"

3. **Increase Docker memory limit:**
   - Docker Desktop → Settings → Resources
   - Set memory to 16-20GB

### Ollama Optimizations

1. **Set environment variables for better performance:**
```powershell
# Add to Windows environment variables
OLLAMA_NUM_PARALLEL=1  # Prevent VRAM overflow
OLLAMA_MAX_LOADED_MODELS=1  # Only keep one model in memory
```

2. **Monitor VRAM usage:**
```powershell
# Watch GPU memory in real-time
nvidia-smi -l 1
```

## Next Steps

- Read [ARCHITECTURE.md](docs/ARCHITECTURE.md) to understand the system design
- Check [API.md](docs/API.md) for API documentation
- Review [SECURITY.md](docs/SECURITY.md) for security best practices
- See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for production deployment

## Support

For issues or questions:
1. Check the logs: `docker-compose logs -f`
2. Verify Ollama is running: `ollama list`
3. Check GPU status: `nvidia-smi`
4. Review Docker Desktop logs
