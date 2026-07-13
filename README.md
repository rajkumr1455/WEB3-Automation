# Web3 Bug Bounty Automation System

A production-ready multi-agent security automation platform for Web3 bug bounty hunting, optimized for Windows with hybrid local/cloud LLM architecture.

## 🚀 Features

- **Multi-Agent Pipeline**: 6 specialized security agents working in sequence
- **Hybrid LLM Architecture**: Local Ollama models + Claude 4.5 for optimal cost/performance
- **Windows Optimized**: Native Ollama with DirectML GPU acceleration (RTX 4060)
- **Comprehensive Analysis**: Static analysis, fuzzing, dynamic monitoring, and AI-powered triage
- **Bug Bounty Ready**: Automated report generation for Immunefi and HackenProof
- **RAG-Enhanced**: Vector database for vulnerability pattern matching
- **Full Observability**: Prometheus + Grafana monitoring stack

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Orchestrator                            │
│              (Sequential Pipeline Controller)                │
└────────────┬────────────────────────────────────────────────┘
             │
    ┌────────┴────────┐
    │   LLM Router    │  ← Routes to Ollama (local) or Claude (cloud)
    └────────┬────────┘
             │
    ┌────────┴────────────────────────────────────────┐
    │                                                  │
┌───▼───┐  ┌──────┐  ┌────────┐  ┌──────────┐  ┌────────┐  ┌──────────┐
│ Recon │→ │Static│→ │Fuzzing │→ │Monitoring│→ │Triage  │→ │Reporting │
└───────┘  └──────┘  └────────┘  └──────────┘  └────────┘  └──────────┘
                                                      │
                                                 ┌────▼────┐
                                                 │  Qdrant │
                                                 │   RAG   │
                                                 └─────────┘
```

## 📋 Prerequisites

- **OS**: Windows 10/11 (64-bit)
- **GPU**: NVIDIA RTX 4060 (8GB VRAM)
- **RAM**: 32GB
- **Storage**: 100GB+ free space
- **Software**:
  - Docker Desktop for Windows
  - Ollama for Windows
  - Git

## ⚡ Quick Start

### 1. Install Dependencies

```powershell
# Install Docker Desktop
# Download from: https://www.docker.com/products/docker-desktop/

# Install Ollama
# Download from: https://ollama.ai/download/windows

# Pull required models
ollama pull deepseek-r1:32b-q4_K_M
ollama pull qwen2.5:14b-instruct-q4_K_M
ollama pull mistral:7b-instruct-q4_K_M
ollama pull nomic-embed-text
```

### 2. Clone and Configure

```powershell
git clone <repo-url> web3_hunter
cd web3_hunter\New

# Copy and edit environment variables
copy .env.example .env
# Edit .env with your API keys
```

### 3. Start the System

```powershell
# Build containers (first time only)
docker-compose build

# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

### 4. Access the Web UI

```powershell
# Open your browser
start http://localhost:3001

# The Web UI provides:
# - Real-time dashboard with system metrics
# - Scan management and monitoring
# - Agent health status
# - Report viewing and generation
# - Settings and configuration
```

### 5. Run Your First Scan

```powershell
# Option 1: Via Web UI
# Navigate to http://localhost:3001 and use the scan form

# Option 2: Via API
# Start a scan
curl -X POST http://localhost:8001/scan `
  -H "Content-Type: application/json" `
  -d '{
    "target_url": "https://github.com/your-org/contract-repo",
    "contract_address": "0x1234...",
    "chain": "ethereum"
  }'

# Check scan status
curl http://localhost:8001/scan/<scan_id>
```

## 🖥️ Web UI

Access the web interface at `http://localhost:3001`

### Available Pages

- **Dashboard** (`/`) - Overview, metrics, and scan management
- **Reconnaissance** (`/recon`) - Repository mapping and surface discovery
- **Static Analysis** (`/static-analysis`) - Slither, Mythril, Semgrep results
- **Fuzzing** (`/fuzzing`) - Foundry and Echidna fuzz results
- **Monitoring** (`/monitoring`) - Real-time mempool and oracle alerts
- **Triage** (`/triage`) - AI-powered vulnerability classification
- **Reports** (`/reports`) - Generated Immunefi/HackenProof reports
- **Agents** (`/agents`) - Microservice health and LLM router status
- **Settings** (`/settings`) - Configuration and preferences

## 🎯 Agent Services

| Agent | Port | Purpose |
|-------|------|---------|
| **Orchestrator** | 8001 | Central pipeline controller |
| **LLM Router** | 8000 | Hybrid LLM request routing |
| **Recon Agent** | 8002 | Repository mapping, ABI extraction |
| **Static Agent** | 8003 | Slither, Mythril, Semgrep analysis |
| **Fuzzing Agent** | 8004 | Foundry fuzz, Echidna, Manticore |
| **Monitoring Agent** | 8005 | Mempool, oracle, RPC monitoring |
| **Triage Agent** | 8006 | Multi-tier AI classification |
| **Reporting Agent** | 8007 | Report generation & notifications |

## 🧠 LLM Strategy

### Local Models (Ollama via host.docker.internal:11434)

- **deepseek-r1:32b-q4_K_M** - Deep reasoning for smart contract analysis
- **qwen2.5:14b-instruct-q4_K_M** - Code analysis and recon
- **mistral:7b-instruct-q4_K_M** - Fast triage and classification
- **nomic-embed-text** - Embeddings for RAG

### Cloud Model (Claude API)

- **claude-4.5-sonnet** - Final reasoning and report synthesis

### Why Hybrid?

- **Cost-effective**: 90% of work done locally
- **Performance**: Local models for fast iteration
- **Quality**: Claude for final high-stakes decisions
- **Privacy**: Sensitive analysis stays local

## 📊 Monitoring

```env
# Required
CLAUDE_API_KEY=sk-ant-xxxxx

# Optional
GITHUB_TOKEN=ghp_xxxxx
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
ETH_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/...
```

### LLM Router Configuration

Edit `services/llm-router/router_config.yaml` to customize task routing.

## 🐛 Troubleshooting

### Ollama Not Accessible

```powershell
# Ensure Ollama is running
ollama serve

# Test connectivity
curl http://localhost:11434/api/tags

# Test from Docker
docker run --rm curlimages/curl curl http://host.docker.internal:11434/api/tags
```

### GPU Not Being Used

```powershell
# Check GPU status
nvidia-smi

# Ollama uses DirectML automatically on Windows
# No additional configuration needed
```

### Out of VRAM

- Models load sequentially to stay within 8GB
- Reduce concurrent scans if needed
- Close other GPU applications

## 🚀 Performance Tips

1. **Disable Windows Defender** for Docker directories
2. **Enable GPU hardware scheduling** in Windows settings
3. **Allocate 16-20GB RAM** to Docker Desktop
4. **Use SSD** for Docker data directory

## 📝 Example Workflow

```powershell
# 1. Start a scan
$scan = Invoke-RestMethod -Uri "http://localhost:8001/scan" -Method Post -Body (@{
    target_url = "https://github.com/compound-finance/compound-protocol"
    chain = "ethereum"
} | ConvertTo-Json) -ContentType "application/json"

# 2. Monitor progress
Invoke-RestMethod -Uri "http://localhost:8001/scan/$($scan.scan_id)"

# 3. View reports (once completed)
Get-Content "data/reports/$($scan.scan_id)_immunefi.md"
Get-Content "data/reports/$($scan.scan_id)_hackenproof.md"
```

## 🤝 Contributing

Contributions welcome! Please read our contributing guidelines first.

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- Ollama for local LLM inference
- Anthropic for Claude API
- Trail of Bits for Slither
- Foundry for fuzzing tools
- Qdrant for vector database

## 📞 Support

- GitHub Issues: Report bugs and request features
- Documentation: Check docs/ directory
- Logs: `docker-compose logs -f`

---

**Built for Windows | Powered by Ollama + Claude | Optimized for RTX 4060**
