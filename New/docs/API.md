# API Documentation

Complete API reference for the Web3 Bug Bounty Automation System.

## Base URLs

- **Orchestrator**: `http://localhost:8001`
- **LLM Router**: `http://localhost:8000`
- **Recon Agent**: `http://localhost:8002`
- **Static Agent**: `http://localhost:8003`
- **Fuzzing Agent**: `http://localhost:8004`
- **Monitoring Agent**: `http://localhost:8005`
- **Triage Agent**: `http://localhost:8006`
- **Reporting Agent**: `http://localhost:8007`

---

## Orchestrator API

### POST /scan

Start a new security scan.

**Request Body**:
```json
{
  "target_url": "https://github.com/org/repo",
  "contract_address": "0x1234567890123456789012345678901234567890",
  "chain": "ethereum",
  "scan_config": {
    "enable_fuzzing": true,
    "monitor_duration": 5
  }
}
```

**Response**:
```json
{
  "scan_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Scan started successfully. Use /scan/{scan_id} to check status."
}
```

### GET /scan/{scan_id}

Get scan status and results.

**Response**:
```json
{
  "scan_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "target_url": "https://github.com/org/repo",
  "contract_address": "0x1234...",
  "started_at": "2025-01-15T10:30:00Z",
  "completed_at": "2025-01-15T10:45:00Z",
  "duration_seconds": 900,
  "results": {
    "recon": { ... },
    "static": { ... },
    "fuzzing": { ... },
    "monitoring": { ... },
    "triage": { ... },
    "reporting": { ... }
  }
}
```

### GET /scans

List recent scans.

**Query Parameters**:
- `limit` (int, default=50): Maximum number of scans to return
- `status` (string, optional): Filter by status (pending/running/completed/failed)

**Response**:
```json
{
  "total": 42,
  "scans": [
    {
      "scan_id": "...",
      "status": "completed",
      "target_url": "...",
      "started_at": "..."
    }
  ]
}
```

### GET /health

Health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "agents": {
    "llm_router": "healthy",
    "recon": "healthy",
    "static": "healthy",
    "fuzzing": "healthy",
    "monitoring": "healthy",
    "triage": "healthy",
    "reporting": "healthy"
  },
  "active_scans": 2
}
```

---

## LLM Router API

### POST /generate

Generate text using appropriate LLM.

**Request Body**:
```json
{
  "task_type": "smart_contract_analysis",
  "prompt": "Analyze this Solidity code...",
  "system_prompt": "You are a security auditor.",
  "max_tokens": 4096,
  "temperature": 0.1
}
```

**Response**:
```json
{
  "response": "Analysis: This contract has...",
  "model_used": "deepseek-r1:32b-q4_K_M",
  "model_type": "local/deep_reasoning",
  "tokens_used": 1234,
  "metadata": {
    "total_duration": 8500000000,
    "load_duration": 1200000000
  }
}
```

### POST /embed

Generate embeddings.

**Request Body**:
```json
{
  "texts": [
    "Smart contract vulnerability description",
    "Another text to embed"
  ]
}
```

**Response**:
```json
{
  "embeddings": [
    [0.123, -0.456, ...],
    [0.789, -0.012, ...]
  ],
  "model_used": "nomic-embed-text",
  "dimensions": 768
}
```

### GET /models

List available models and routing configuration.

**Response**:
```json
{
  "local_models": {
    "deep_reasoning": { ... },
    "code_analysis": { ... },
    "fast_triage": { ... },
    "embeddings": { ... }
  },
  "cloud_models": {
    "final_reasoning": { ... }
  },
  "routing_rules": [ ... ]
}
```

---

## Recon Agent API

### POST /scan

Perform reconnaissance.

**Request Body**:
```json
{
  "target_url": "https://github.com/org/repo",
  "contract_address": "0x1234...",
  "chain": "ethereum"
}
```

**Response**:
```json
{
  "target_url": "https://github.com/org/repo",
  "repository_info": {
    "has_contracts": true,
    "has_frontend": true,
    "has_backend": false,
    "contract_files": ["contracts/Token.sol"],
    "languages": ["Solidity"],
    "frameworks": ["Foundry"]
  },
  "contracts": [
    {
      "file": "contracts/Token.sol",
      "source": "pragma solidity ^0.8.0;...",
      "language": "Solidity"
    }
  ],
  "abis": [
    {
      "address": "0x1234...",
      "abi": [...],
      "verified": true
    }
  ],
  "dns_records": [...],
  "rpc_endpoints": ["https://eth-mainnet.g.alchemy.com/..."],
  "surface_map": {
    "analysis": "This project has...",
    "contract_count": 5,
    "has_frontend": true
  }
}
```

---

## Static Analysis Agent API

### POST /analyze

Perform static analysis.

**Request Body**:
```json
{
  "scan_id": "550e8400-...",
  "contracts": [
    {
      "file": "Token.sol",
      "source": "pragma solidity ^0.8.0;..."
    }
  ],
  "source_code": {}
}
```

**Response**:
```json
{
  "scan_id": "550e8400-...",
  "slither_findings": [...],
  "mythril_findings": [...],
  "semgrep_findings": [...],
  "ai_summary": "Critical vulnerabilities found...",
  "total_issues": 15,
  "critical_count": 2,
  "high_count": 5,
  "medium_count": 6,
  "low_count": 2
}
```

---

## Fuzzing Agent API

### POST /fuzz

Perform fuzzing.

**Request Body**:
```json
{
  "scan_id": "550e8400-...",
  "contracts": [...],
  "abis": [...]
}
```

**Response**:
```json
{
  "scan_id": "550e8400-...",
  "foundry_results": [
    {
      "contract": "Token",
      "tests": [...],
      "total": 10,
      "failed": 2
    }
  ],
  "mutation_results": [...],
  "total_tests": 10,
  "failed_tests": 2,
  "coverage_percent": 85.5
}
```

---

## Monitoring Agent API

### POST /monitor

Perform dynamic monitoring.

**Request Body**:
```json
{
  "scan_id": "550e8400-...",
  "contract_address": "0x1234...",
  "chain": "ethereum",
  "duration_minutes": 5
}
```

**Response**:
```json
{
  "scan_id": "550e8400-...",
  "contract_address": "0x1234...",
  "mempool_anomalies": [
    {
      "type": "large_value_transfer",
      "tx_hash": "0xabc...",
      "value": "10000000000000000000",
      "from": "0x5678...",
      "timestamp": "2025-01-15T10:35:00Z"
    }
  ],
  "oracle_deviations": [],
  "rpc_drift": [],
  "suspicious_transactions": [],
  "total_anomalies": 1
}
```

---

## Triage Agent API

### POST /triage

Perform multi-tier triage.

**Request Body**:
```json
{
  "scan_id": "550e8400-...",
  "findings": {
    "static": {...},
    "fuzzing": {...},
    "monitoring": {...}
  }
}
```

**Response**:
```json
{
  "scan_id": "550e8400-...",
  "vulnerabilities": [
    {
      "title": "Reentrancy in withdraw function",
      "severity": "critical",
      "confidence": "high",
      "description": "The withdraw function...",
      "impact": "Attacker can drain contract funds...",
      "recommendation": "Implement checks-effects-interactions pattern...",
      "reproduction_steps": [
        "Deploy malicious contract",
        "Call withdraw with callback"
      ],
      "immunefi_severity": "Critical",
      "hackenproof_severity": "P1 - Critical",
      "cvss_score": 9.8
    }
  ],
  "total_vulnerabilities": 3,
  "critical_count": 1,
  "high_count": 2,
  "medium_count": 0,
  "low_count": 0,
  "triage_summary": "Triage complete: 3 vulnerabilities confirmed..."
}
```

---

## Reporting Agent API

### POST /generate

Generate reports and notifications.

**Request Body**:
```json
{
  "scan_id": "550e8400-...",
  "target_url": "https://github.com/org/repo",
  "contract_address": "0x1234...",
  "findings": {...}
}
```

**Response**:
```json
{
  "scan_id": "550e8400-...",
  "immunefi_report_path": "/app/reports/550e8400_immunefi.md",
  "hackenproof_report_path": "/app/reports/550e8400_hackenproof.md",
  "json_report_path": "/app/reports/550e8400_full.json",
  "github_issue_url": "https://github.com/org/repo/issues/42",
  "slack_notified": true
}
```

---

## Error Responses

All endpoints return standard error responses:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common HTTP Status Codes**:
- `200 OK`: Success
- `400 Bad Request`: Invalid input
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Dependent service unavailable

---

## Rate Limiting

Currently no rate limiting is implemented. For production:
- Implement API gateway (Kong, Tyk)
- Set per-user rate limits
- Monitor via Prometheus

---

## Authentication

Currently no authentication is required. For production:
- Implement JWT-based authentication
- API key management
- Role-based access control (RBAC)

---

## Webhooks (Future)

Planned webhook support for scan completion:

```json
POST https://your-server.com/webhook
{
  "event": "scan.completed",
  "scan_id": "550e8400-...",
  "status": "completed",
  "vulnerabilities_count": 3,
  "timestamp": "2025-01-15T10:45:00Z"
}
```

---

## SDK Examples

### Python

```python
import requests

# Start scan
response = requests.post(
    "http://localhost:8001/scan",
    json={
        "target_url": "https://github.com/org/repo",
        "chain": "ethereum"
    }
)
scan_id = response.json()["scan_id"]

# Check status
status = requests.get(f"http://localhost:8001/scan/{scan_id}").json()
print(f"Status: {status['status']}")
```

### PowerShell

```powershell
# Start scan
$body = @{
    target_url = "https://github.com/org/repo"
    chain = "ethereum"
} | ConvertTo-Json

$scan = Invoke-RestMethod -Uri "http://localhost:8001/scan" `
    -Method Post -Body $body -ContentType "application/json"

# Check status
$status = Invoke-RestMethod -Uri "http://localhost:8001/scan/$($scan.scan_id)"
Write-Host "Status: $($status.status)"
```

### cURL

```bash
# Start scan
curl -X POST http://localhost:8001/scan \
  -H "Content-Type: application/json" \
  -d '{
    "target_url": "https://github.com/org/repo",
    "chain": "ethereum"
  }'

# Check status
curl http://localhost:8001/scan/{scan_id}
```
