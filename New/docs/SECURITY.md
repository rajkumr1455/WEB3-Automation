# Security Hardening Guide

## Overview

This guide covers security best practices for deploying and operating the Web3 Bug Bounty Automation System.

## Network Security

### Docker Network Isolation

**Current Setup**:
- All services communicate via internal `web3-net` bridge network
- Only Orchestrator port (8001) exposed to host
- LLM Router not directly accessible from outside

**Recommendations**:

1. **Use Docker secrets for sensitive data**:
```yaml
secrets:
  claude_api_key:
    external: true

services:
  llm-router:
    secrets:
      - claude_api_key
```

2. **Implement reverse proxy** (Nginx, Traefik):
```nginx
server {
    listen 443 ssl;
    server_name bounty.example.com;
    
    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;
    
    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
    }
}
```

3. **Enable TLS** for all external communications

### Firewall Configuration

**Windows Firewall**:
```powershell
# Allow only localhost access to Orchestrator
New-NetFirewallRule -DisplayName "Web3 Orchestrator" `
    -Direction Inbound -LocalPort 8001 -Protocol TCP `
    -Action Allow -RemoteAddress 127.0.0.1
```

**Production**: Use cloud provider firewall (AWS Security Groups, Azure NSG)

## Authentication & Authorization

### API Authentication

**Implement JWT-based auth**:

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    # Verify JWT token
    if not is_valid_token(token):
        raise HTTPException(status_code=401, detail="Invalid token")
    return token

@app.post("/scan")
async def start_scan(request: ScanRequest, token: str = Depends(verify_token)):
    # Protected endpoint
    pass
```

### API Keys

**For production**:
1. Generate unique API keys per user
2. Store hashed in database
3. Implement key rotation
4. Rate limit per key

## Secrets Management

### Environment Variables

**Never commit secrets to Git**:
```gitignore
.env
*.key
*.pem
secrets/
```

**Use secret management tools**:
- **Docker Secrets** (Swarm mode)
- **Kubernetes Secrets**
- **HashiCorp Vault**
- **AWS Secrets Manager**
- **Azure Key Vault**

### Ollama API Security

**Ollama runs locally** - no authentication by default.

**Recommendations**:
1. **Never expose Ollama port (11434) to internet**
2. **Use firewall to restrict access**:
```powershell
# Block external access to Ollama
New-NetFirewallRule -DisplayName "Block Ollama External" `
    -Direction Inbound -LocalPort 11434 -Protocol TCP `
    -Action Block -RemoteAddress !127.0.0.1
```

### Claude API Key Protection

**Best practices**:
1. **Use environment variables** (never hardcode)
2. **Rotate keys regularly** (every 90 days)
3. **Monitor usage** via Anthropic dashboard
4. **Set spending limits**
5. **Use separate keys** for dev/staging/prod

## Input Validation

### Scan Request Validation

**Validate all inputs**:

```python
from pydantic import BaseModel, validator, HttpUrl

class ScanRequest(BaseModel):
    target_url: HttpUrl  # Validates URL format
    contract_address: Optional[str]
    chain: str
    
    @validator('contract_address')
    def validate_address(cls, v):
        if v and not re.match(r'^0x[a-fA-F0-9]{40}$', v):
            raise ValueError('Invalid Ethereum address')
        return v
    
    @validator('chain')
    def validate_chain(cls, v):
        allowed = ['ethereum', 'bsc', 'polygon', 'arbitrum']
        if v not in allowed:
            raise ValueError(f'Chain must be one of {allowed}')
        return v
```

### Repository Cloning Safety

**Prevent malicious repositories**:

```python
async def clone_repository(url: str) -> Optional[Path]:
    # Validate URL
    if not url.startswith(('https://github.com/', 'https://gitlab.com/')):
        raise ValueError("Only GitHub and GitLab URLs allowed")
    
    # Clone with depth limit
    git.Repo.clone_from(url, clone_path, depth=1, single_branch=True)
    
    # Scan for malicious files
    for file_path in clone_path.rglob("*"):
        if file_path.suffix in ['.exe', '.dll', '.so']:
            raise ValueError("Suspicious file detected")
```

## Code Execution Safety

### Sandboxing

**Static analysis tools run in Docker containers** - already sandboxed.

**Additional safety**:
1. **Resource limits**:
```yaml
services:
  static-agent:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

2. **Read-only filesystem** where possible:
```yaml
services:
  static-agent:
    read_only: true
    tmpfs:
      - /tmp
```

### Foundry Fuzzing Safety

**Never run on mainnet**:
```solidity
// Always use forked testnet
forge test --fork-url $TESTNET_RPC_URL
```

**Limit gas**:
```toml
[profile.default]
gas_limit = 30000000
```

## Data Privacy

### Sensitive Code Handling

**Local LLMs for sensitive analysis**:
- Smart contract code stays local (Ollama)
- Only summaries sent to Claude
- No code in logs

**Recommendations**:
1. **Encrypt data at rest** (Docker volumes)
2. **Use TLS for all network traffic**
3. **Implement data retention policies**
4. **Anonymize logs**

### Report Storage

**Secure report storage**:
```python
import os
from cryptography.fernet import Fernet

# Encrypt reports before storage
key = os.getenv("ENCRYPTION_KEY")
cipher = Fernet(key)

encrypted_report = cipher.encrypt(report.encode())
```

## Monitoring & Logging

### Security Logging

**Log security events**:
```python
import logging

security_logger = logging.getLogger('security')

# Log authentication attempts
security_logger.info(f"Auth attempt: {user_id} from {ip_address}")

# Log scan requests
security_logger.info(f"Scan started: {scan_id} by {user_id}")

# Log errors
security_logger.error(f"Unauthorized access attempt: {ip_address}")
```

### Audit Trail

**Track all actions**:
- Who started each scan
- What was scanned
- When it was scanned
- Results accessed

### Alerting

**Set up alerts for**:
- Failed authentication attempts
- Unusual scan patterns
- High error rates
- Resource exhaustion

## Dependency Security

### Vulnerability Scanning

**Scan Docker images**:
```bash
# Using Trivy
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image llm-router:latest
```

**Scan Python dependencies**:
```bash
pip install safety
safety check
```

### Keep Dependencies Updated

```bash
# Update base images regularly
docker-compose pull
docker-compose build --no-cache

# Update Python packages
pip install --upgrade -r requirements.txt
```

## Rate Limiting

### Prevent Abuse

**Implement rate limiting**:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/scan")
@limiter.limit("10/hour")  # 10 scans per hour per IP
async def start_scan(request: ScanRequest):
    pass
```

## Incident Response

### Preparation

1. **Document procedures** for security incidents
2. **Maintain contact list** for security team
3. **Regular backups** of critical data
4. **Disaster recovery plan**

### Detection

**Monitor for**:
- Unusual API usage patterns
- Unexpected errors
- Resource exhaustion
- Unauthorized access attempts

### Response

1. **Isolate affected systems**
2. **Preserve evidence** (logs, memory dumps)
3. **Notify stakeholders**
4. **Patch vulnerabilities**
5. **Post-mortem analysis**

## Compliance

### Data Protection

**GDPR compliance** (if applicable):
- Data minimization
- Right to erasure
- Data portability
- Consent management

### Bug Bounty Platform Requirements

**Immunefi**:
- Responsible disclosure
- No public disclosure before fix
- Safe reproduction only

**HackenProof**:
- Follow platform guidelines
- Proper severity classification
- Clear reproduction steps

## Security Checklist

### Pre-Deployment

- [ ] All secrets in environment variables
- [ ] TLS enabled for external communications
- [ ] Firewall rules configured
- [ ] Authentication implemented
- [ ] Input validation in place
- [ ] Rate limiting configured
- [ ] Logging and monitoring set up
- [ ] Backups configured
- [ ] Incident response plan documented

### Post-Deployment

- [ ] Regular security audits
- [ ] Dependency updates
- [ ] Log review
- [ ] Access control review
- [ ] Penetration testing
- [ ] Compliance verification

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
