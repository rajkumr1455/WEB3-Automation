# Guardrail Auto-Pause System

Real-time transaction monitoring system that can automatically pause smart contracts when exploits are detected.

## Features

- **Mempool Monitoring**: Watch pending transactions in real-time
- **Transaction Simulation**: Simulate transactions before execution to detect exploits
- **Exploit Detection**: Identify common attack patterns:
  - Reentrancy attacks
  - Flash loan exploits
  - Price manipulation
  - Access control bypasses
  - Unusual token transfers
- **Auto-Pause**: Automatically pause contracts when critical threats detected
- **Manual Approval**: Optional

 manual approval workflow for pause requests
- **Multi-Channel Alerts**: API, Slack, Email notifications

## Architecture

```
Blockchain Mempool
       ↓
 Mempool Monitor
       ↓
Transaction Simulator ← Exploit Pattern Detection
       ↓
  Risk Assessment
       ↓
Pause Manager (Manual/Auto)
       ↓
   Alert System
```

## API Endpoints

### Start Monitoring
```http
POST /monitor/start
Content-Type: application/json

{
  "contract_address": "0x...",
  "chain": "ethereum",
  "auto_pause": false,
  "alert_channels": ["api", "slack"]
}
```

### Stop Monitoring
```http
POST /monitor/stop?contract_address=0x...
```

### Get Monitoring Status
```http
GET /monitor/status
```

### Request Contract Pause
```http
POST /pause/request
Content-Type: application/json

{
  "contract_address": "0x...",
  "reason": "Exploit detected",
  "severity": "critical",
  "auto_approved": false
}
```

### Approve Pause Request
```http
POST /pause/approve/{pause_id}
```

### Get All Pause Requests
```http
GET /pause/requests
```

## Configuration

Environment variables:
```env
ETH_RPC_URL=https://eth.llamarpc.com
BSC_RPC_URL=https://bsc-dataseed.binance.org
POLYGON_RPC_URL=https://polygon-rpc.com
```

## Usage

### Basic Monitoring
```python
import httpx

# Start monitoring
response = await httpx.post(
    "http://localhost:8009/monitor/start",
    json={
        "contract_address": "0x1234...",
        "chain": "ethereum",
        "auto_pause": False  # Manual approval required
    }
)
```

### Auto-Pause Mode
```python
# Start with auto-pause enabled
response = await httpx.post(
    "http://localhost:8009/monitor/start",
    json={
        "contract_address": "0x1234...",
        "auto_pause": True  # Will pause automatically on exploit
    }
)
```

## Production Setup

### 1. Full Node Access
For production mempool monitoring, you need:
- Full Ethereum node with `txpool` access
- Or use services like:
  - Blocknative Mempool API
  - Alchemy Enhanced APIs
  - QuickNode with mempool streaming

### 2. Transaction Simulation
Integrate with:
- **Tenderly**: Simulation API
- **Hardhat**: Local forking
- **Custom EVM**: Build your own simulator

### 3. Pause Mechanism
Implement contract pausing via:
- **Gnosis Safe**: Multi-sig transactions
- **Defender**: Automated responses
- **Custom**: Direct web3 calls

## Limitations

**Current Implementation:**
- Simplified mempool monitoring (requires full node)
- Basic pattern detection (not ML-based)
- Manual pause execution (not automated)

**Production Requirements:**
- WebSocket connection to mempool
- Advanced pattern detection with ML
- Automated pause transaction execution
- Multi-sig integration
- Rate limiting and caching

## Future Enhancements

- [ ] ML-based exploit detection
- [ ] Integration with Tenderly/Hardhat
- [ ] Multi-sig pause execution
- [ ] Historical transaction analysis
- [ ] Gas optimization attacks detection
- [ ] MEV exploitation detection
- [ ] Cross-chain monitoring

## Security Considerations

> [!CAUTION]
> Auto-pause functionality can be weaponized. Always use multi-sig and governance controls in production.

**Best Practices:**
1. Use multi-sig for pause authority
2. Implement timelock for pause execution
3. Add governance voting for critical decisions
4. Monitor pause requests for abuse
5. Set up alerts for false positives

## License

MIT
