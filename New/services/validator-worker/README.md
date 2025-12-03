# Validator Worker

Automated validation and reproduction service for security findings.

## Features

- **Finding Reproduction**: Automatically reproduce security vulnerabilities
- **Sandboxed Execution**: Safe isolated environments using Docker/Foundry
- **Trace Capture**: Detailed execution traces and state diffs
- **Confidence Scoring**: ML-based confidence assessment
- **Queue System**: Background processing for scalability
- **Manual Override**: Human-in-the-loop for edge cases

## Architecture

```
Finding Input
      ↓
  Queue System
      ↓
Sandbox Creation (Foundry/Hardhat/Docker)
      ↓
PoC Execution
      ↓
Trace Analysis
      ↓
Validation Result (Valid/Invalid + Confidence)
      ↓
ML-Ops Feedback Loop
```

## API Endpoints

### Submit Finding for Validation
```http
POST /validate
Content-Type: application/json

{
  "finding": {
    "id": "finding-123",
    "type": "reentrancy",
    "severity": "critical",
    "title": "Reentrancy in withdraw()",
    "description": "...",
   "proof_of_concept": "// Solidity PoC code"
  },
  "chain": "ethereum",
  "timeout": 300,
  "sandbox_type": "foundry"
}
```

**Response:**
```json
{
  "job_id": "uuid",
  "finding_id": "finding-123",
  "status": "queued",
  "started_at": "2024-11-30T..."
}
```

### Get Validation Status
```http
GET /validate/{job_id}
```

**Response:**
```json
{
  "job_id": "uuid",
  "finding_id": "finding-123",
  "status": "completed",
  "is_valid": true,
  "confidence": 0.95,
  "execution_trace": "...",
  "completed_at": "2024-11-30T..."
}
```

### List All Validations
```http
GET /validations
```

### Manual Override
```http
POST /validate/{job_id}/mark?is_valid=true&confidence=0.9
```

## Sandbox Types

### Foundry (Default)
- Fast Solidity testing framework
- Built-in fuzzing
- Great for EVM contracts

### Hardhat
- JavaScript/TypeScript testing
- More flexibility
- Good for complex scenarios

### Docker
- Complete isolation
- Multi-language support
- Slower but most secure

## Proof of Concept Templates

The service includes built-in PoC templates for common vulnerabilities:

### Reentrancy
```solidity
function test_exploit() public {
    target.deposit{value: 1 ether}();
    target.withdraw(1 ether);
}

receive() external payable {
    if (address(target).balance >= 1 ether) {
        target.withdraw(1 ether);
    }
}
```

### Integer Overflow
```solidity
function test_exploit() public {
    uint256 largeValue = type(uint256).max;
    target.vulnerableFunction(largeValue);
}
```

### Access Control
```solidity
function test_exploit() public {
    vm.prank(attacker);
    target.privilegedFunction();
}
```

## Usage

### Validate a Finding
```python
import httpx

# Submit validation request
response = await httpx.post(
    "http://localhost:8010/validate",
    json={
        "finding": {
            "id": "find-001",
            "type": "reentrancy",
            "severity": "critical",
            "title": "Reentrancy Vulnerability",
            "description": "Withdraw function is vulnerable",
            "proof_of_concept": "// PoC code here"
        },
        "timeout": 300
    }
)

job = response.json()
job_id = job["job_id"]

# Poll for results
while True:
    status_response = await httpx.get(
        f"http://localhost:8010/validate/{job_id}"
    )
    status = status_response.json()
    
    if status["status"] == "completed":
        if status["is_valid"]:
            print(f"Vulnerability confirmed! Confidence: {status['confidence']}")  
        else:
            print("False positive detected")
        break
    
    await asyncio.sleep(5)
```

## Production Setup

### 1. Install Foundry
```bash
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

### 2. Configure Sandboxes
```env
MAX_CONCURRENT_VALIDATIONS=5
SANDBOX_TIMEOUT=300
FOUNDRY_PROFILE=production
```

### 3. Resource Limits
Set appropriate Docker resource limits:
```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
```

## Security Considerations

> [!CAUTION]
> Validator executes untrusted code. Always run in isolated environments.

**Best Practices:**
1. Use Docker for complete isolation
2. Set strict resource limits
3. Implement timeout mechanisms
4. Monitor for malicious PoCs
5. Sandbox network access
6. Regular security audits

## Limitations

**Current Implementation:**
- Simplified PoC templates
- Limited to Foundry sandboxes
- Basic trace analysis
- No state diff extraction

**Production Requirements:**
- Advanced PoC generation (AI-assisted)
- Multi-framework support
- Deep trace analysis with symbolic execution
- State diff capture and comparison
- Gas optimization detection
- Network simulation for DeFi protocols

## Integration with ML-Ops

Validated findings feed into the ML-Ops engine:

```python
# After validation
if validation_result["is_valid"]:
    await mlops.train_on_validated_finding(finding, trace)
else:
    await mlops.mark_false_positive(finding)
```

## Future Enhancements

- [ ] AI-powered PoC generation
- [ ] Symbolic execution integration
- [ ] Multi-chain support (Solana, Aptos, etc.)
- [ ] Fuzzing integration
- [ ] Historical exploit database
- [ ] Automatic fix suggestion
- [ ] Integration with bug bounty platforms

## License

MIT
