# RPC Connection Pool Integration Guide

This guide explains how to integrate the RPC connection pool into your services for automatic failover and health monitoring.

## Overview

The RPC connection pool provides:
- **Automatic failover** to backup providers
- **Health monitoring** with periodic checks
- **Circuit breaker** pattern (auto-disable failing providers)
- **Retry logic** with exponential backoff

## Configuration

### 1. Update `.env` file

Add primary and backup RPC URLs for each chain:

```bash
# Primary RPCs
ETHEREUM_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY
BSC_RPC_URL=https://bsc-dataseed.binance.org/
POLYGON_RPC_URL=https://polygon-rpc.com/

# Backup RPCs (for failover)
ETHEREUM_RPC_URL_BACKUP=https://mainnet.infura.io/v3/YOUR_KEY
BSC_RPC_URL_BACKUP=https://rpc.ankr.com/bsc
POLYGON_RPC_URL_BACKUP=https://polygon-mainnet.public.blastapi.io
```

### 2. Import and Initialize

```python
from src.utils.rpc_connection_pool import RPCConnectionPool
import os

# Create pool with primary + backup
pool = RPCConnectionPool(
    providers=[
        os.getenv("ETHEREUM_RPC_URL"),
        os.getenv("ETHEREUM_RPC_URL_BACKUP")
    ],
    health_check_interval=60,  # Check every 60s
    circuit_breaker_threshold=5,  # Open after 5 failures
    circuit_breaker_timeout=300  # Retry after 5 minutes
)

# Start background health checks
await pool.start()
```

### 3. Use Pool for RPC Calls

#### Option A: Get Web3 Instance

```python
# Get Web3 connected to best available provider
w3 = pool.get_web3()

# Use normally
block = w3.eth.get_block('latest')
balance = w3.eth.get_balance('0xAddress...')
```

#### Option B: Execute JSON-RPC Directly

```python
# Automatic failover on errors
block_number = await pool.get_block_number()
balance = await pool.get_balance('0xAddress...')

# Custom RPC method
result = await pool.execute_with_failover(
    method="eth_getTransactionReceipt",
    params=["0xTxHash..."]
)
```

### 4. Monitor Pool Health

```python
# Get current pool status
status = pool.get_status()

print(f"Healthy providers: {status['healthy']}/{status['total_providers']}")
print(f"Circuit breakers open: {status['circuit_open']}")

# Check individual providers
for provider in status['providers']:
    print(f"{provider['url'][:50]}: {provider['status']}")
```

### 5. Cleanup on Shutdown

```python
# Stop health check background task
await pool.stop()
```

## Integration Examples

### Example 1: Monitoring Agent (DONE ✅)

See: `services/monitoring-agent/app.py`

```python
# Initialize pools for all chains at startup
RPC_POOLS = {}

@app.on_event("startup")
async def startup_event():
    chains = ["ethereum", "bsc", "polygon"]
    for chain in chains:
        RPC_POOLS[chain] = RPCConnectionPool(
            providers=[
                os.getenv(f"{chain.upper()}_RPC_URL"),
                os.getenv(f"{chain.upper()}_RPC_URL_BACKUP")
            ]
        )
        await RPC_POOLS[chain].start()

# Use in endpoint
@app.post("/monitor")
async def monitor(request: MonitorRequest):
    pool = RPC_POOLS[request.chain]
    block = await pool.get_block_number()
    # ... rest of logic
```

### Example 2: Orchestrator (TODO)

Update `services/orchestrator/app.py`:

```python
from src.utils.rpc_connection_pool import RPCConnectionPool

# Initialize global RPC pool
ETHEREUM_RPC_POOL = None

@app.on_event("startup")
async def startup_event():
    global ETHEREUM_RPC_POOL
    ETHEREUM_RPC_POOL = RPCConnectionPool(
        providers=[
            os.getenv("ETHEREUM_RPC_URL"),
            os.getenv("ETHEREUM_RPC_URL_BACKUP")
        ]
    )
    await ETHEREUM_RPC_POOL.start()
    logger.info("RPC pool initialized")

@app.on_event("shutdown")
async def shutdown_event():
    if ETHEREUM_RPC_POOL:
        await ETHEREUM_RPC_POOL.stop()

# Use in scan pipeline
async def verify_contract_bytecode(address: str):
    """Verify contract hasn't changed"""
    try:
        # Get code with automatic failover
        w3 = ETHEREUM_RPC_POOL.get_web3()
        bytecode = w3.eth.get_code(address)
        return bytecode.hex()
    except Exception as e:
        logger.error(f"Bytecode verification failed: {e}")
        raise
```

### Example 3: Address Scanner (TODO)

Update `services/address-scanner/app.py`:

```python
# Replace direct Web3 initialization with pool
class ExplorerFetcher:
    def __init__(self, chain: Chain):
        self.chain = chain
        self.rpc_pool = RPCConnectionPool(
            providers=[
                os.getenv(f"{chain.name}_RPC_URL"),
                os.getenv(f"{chain.name}_RPC_URL_BACKUP")
            ]
        )
    
    async def fetch_contract_data(self, address: str):
        # Use pool for all RPC calls
        w3 = self.rpc_pool.get_web3()
        code = w3.eth.get_code(address)
        # ... rest of logic
```

## Testing Failover

### Manual Test

```python
# Test failover by using invalid primary
pool = RPCConnectionPool(
    providers=[
        "http://invalid-rpc:8545",  # Will fail
        "https://ethereum.publicnode.com"  # Should failover here
    ]
)

await pool.start()

# This should succeed via backup
block = await pool.get_block_number()
print(f"Block: {block} (via failover)")

# Check status
status = pool.get_status()
print(f"Primary: {status['providers'][0]['status']}")  # FAILED
print(f"Backup: {status['providers'][1]['status']}")   # HEALTHY
```

### Integration Test

Create `tests/integration/test_rpc_pool_integration.py`:

```python
import pytest
from src.utils.rpc_connection_pool import RPCConnectionPool
import os

@pytest.mark.asyncio
async def test_rpc_pool_failover():
    """Test automatic failover to backup provider"""
    pool = RPCConnectionPool(
        providers=[
            "http://invalid-endpoint:8545",
            os.getenv("ETHEREUM_RPC_URL", "https://ethereum.publicnode.com")
        ]
    )
    
    await pool.start()
    
    try:
        # Should succeed despite invalid primary
        block = await pool.get_block_number()
        assert block > 0
        
        # Verify failover occurred
        status = pool.get_status()
        assert status['healthy'] == 1
        assert status['failed'] >= 1
        
    finally:
        await pool.stop()

@pytest.mark.asyncio
async def test_rpc_pool_circuit_breaker():
    """Test circuit breaker opens after threshold"""
    pool = RPCConnectionPool(
        providers=["http://invalid:8545"],
        circuit_breaker_threshold=3
    )
    
    # Trigger failures
    for _ in range(5):
        try:
            await pool.get_block_number()
        except:
            pass
    
    status = pool.get_status()
    assert status['circuit_open'] == 1
```

## Troubleshooting

### Issue: "All RPC providers failed"

**Cause**: Both primary and backup are unavailable.

**Solution**:
1. Check `.env` has valid RPC URLs
2. Verify RPCs are reachable: `curl https://your-rpc-url`
3. Check pool status: `pool.get_status()`
4. Increase circuit breaker timeout

### Issue: "Circuit breaker open"

**Cause**: Provider failed 5+ times, circuit breaker engaged.

**Solution**:
- Wait 5 minutes for auto-recovery
- Check provider health manually
- Use `/rpc-status` endpoint to monitor

### Issue: Slow failover

**Cause**: Health check interval too long.

**Solution**:
```python
pool = RPCConnectionPool(
    providers=[...],
    health_check_interval=30  # Check every 30s instead of 60s
)
```

## Monitoring & Observability

### Prometheus Metrics (Future)

Add to `src/utils/rpc_connection_pool.py`:

```python
from prometheus_client import Counter, Gauge

RPC_REQUESTS = Counter('rpc_requests_total', 'Total RPC requests', ['provider', 'status'])
RPC_LATENCY = Histogram('rpc_request_duration_seconds', 'RPC request latency')
RPC_POOL_HEALTHY = Gauge('rpc_pool_healthy_providers', 'Number of healthy providers', ['chain'])
```

### Logging

Pool already logs key events:
- Provider selection
- Failover occurrences
- Circuit breaker state changes
- Health check results

Check logs:
```bash
docker-compose logs -f monitoring-agent | grep "RPC"
```

## Migration Checklist

- [x] Update `.env.example` with RPC backup URLs
- [x] Update monitoring-agent to use pool
- [ ] Update orchestrator to use pool
- [ ] Update address-scanner to use pool  
- [ ] Update guardrail service to use pool
- [ ] Add integration tests
- [ ] Update documentation
- [ ] Deploy to testnet
- [ ] Monitor failover metrics

## Next Steps

1. **Test in development**:
   ```bash
   # Update .env with your RPC URLs
   docker-compose up -d monitoring-agent
   docker-compose logs -f monitoring-agent
   ```

2. **Verify failover**:
   ```bash
   curl http://localhost:8005/rpc-status
   ```

3. **Integrate into remaining services** (orchestrator, address-scanner, guardrail)

4. **Add monitoring dashboards** (Grafana panels for RPC health)

---

**Questions?** See [src/utils/rpc_connection_pool.py](file:///c:/Users/patel/Desktop/web3_hunter/New/src/utils/rpc_connection_pool.py) for full API documentation.
