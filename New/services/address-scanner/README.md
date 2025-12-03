# Address Scanner Service

Multi-chain smart contract scanner that works with blockchain addresses directly, without requiring GitHub repositories.

## Features

- **Multi-Chain Support**: Ethereum, BSC, Polygon, Arbitrum, Optimism, Solana, Aptos, Sui, Starknet
- **Auto-Detection**: Automatically detects blockchain from address format
- **Source Fetching**: Retrieves verified source code from block explorers
- **Static Analysis**: Integrates with existing static-agent for vulnerability detection
- **RESTful API**: Easy-to-use FastAPI endpoints

## Supported Blockchains

| Blockchain | Address Format | Example |
|------------|----------------|---------|
| Ethereum | 0x + 40 hex | `0x1234...abcd` (42 chars) |
| Binance Smart Chain | 0x + 40 hex | `0x1234...abcd` (42 chars) |
| Polygon | 0x + 40 hex | `0x1234...abcd` (42 chars) |
| Arbitrum | 0x + 40 hex | `0x1234...abcd` (42 chars) |
| Optimism | 0x + 40 hex | `0x1234...abcd` (42 chars) |
| Solana | Base58 | 32-44 chars, no 0x prefix |
| Aptos | 0x + 64 hex | `0x1234...abcd` (66 chars) |
| Sui | 0x + 64 hex | `0x1234...abcd` (66 chars) |
| Starknet | 0x + variable | 50+ chars |

## API Endpoints

### Scan Address
```http
POST /scan-address
Content-Type: application/json

{
  "address": "0x1234567890abcdef1234567890abcdef12345678",
  "chain": "ethereum",  // optional, will auto-detect
  "rpc_url": "https://eth.llamarpc.com",  // optional
  "force_decompile": false  // optional
}
```

**Response:**
```json
{
  "scan_id": "uuid-here",
  "address": "0x...",
  "chain": "ethereum",
  "source_found": true,
  "decompiled": false,
  "findings": [...],
  "status": "completed"
}
```

### Get Supported Chains
```http
GET /supported-chains
```

### Health Check
```http
GET /health
```

## Environment Variables

Create a `.env` file with API keys for block explorers:

```env
ETHERSCAN_API_KEY=your_etherscan_key
BSCSCAN_API_KEY=your_bscscan_key
POLYGONSCAN_API_KEY=your_polygonscan_key
ARBISCAN_API_KEY=your_arbiscan_key
OPTIMISM_API_KEY=your_optimism_key
```

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
uvicorn app:app --host 0.0.0.0 --port 8008 --reload
```

## Running with Docker

```bash
# Build
docker build -t address-scanner .

# Run
docker run -p 8008:8008 --env-file .env address-scanner
```

## Integration with Docker Compose

The service is automatically included in the main `docker-compose.yml`:

```yaml
address-scanner:
  build: ./services/address-scanner
  ports:
    - "8008:8008"
  environment:
    - ETHERSCAN_API_KEY=${ETHERSCAN_API_KEY}
  networks:
    - web3-network
```

## Usage Examples

### Scan Ethereum Contract
```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8008/scan-address",
        json={
            "address": "0x1234567890abcdef1234567890abcdef12345678"
        }
    )
    result = response.json()
    print(f"Found {len(result['findings'])} issues")
```

### Check Supported Chains
```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.get("http://localhost:8008/supported-chains")
    chains = response.json()
    print(f"Supported: {chains['chains']}")
```

## Future Enhancements

- [ ] Bytecode decompilation for unverified contracts
- [ ] Solana program analysis
- [ ] Aptos/Sui Move analysis
- [ ] Starknet Cairo analysis
- [ ] Historical transaction analysis
- [ ] Gas usage optimization detection
- [ ] MEV vulnerability scanning

## Architecture

```
services/address-scanner/
├── app.py                      # Main FastAPI application
├── detectors/
│   └── chain_detector.py       # Auto-detect blockchain
├── fetchers/
│   └── explorer_fetcher.py     # Fetch source from explorers
├── decompilers/
│   └── (future enhancement)
├── requirements.txt
├── Dockerfile
└── README.md
```

## Contributing

1. Add support for new blockchains in `detectors/chain_detector.py`
2. Add explorer APIs in `fetchers/explorer_fetcher.py`
3. Implement decompilers in `decompilers/` directory
4. Update tests and documentation

## License

MIT
