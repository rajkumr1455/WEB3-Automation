# Web3 Hunter - Configuration Guide

This guide explains how to configure Web3 Hunter with your API keys and settings.

## Quick Setup

### Step 1: Choose Your Configuration Method

You can configure Web3 Hunter using either:
1. **`.env` file** (Recommended for API keys)
2. **`config/settings.yaml`** (For both API keys and settings)

### Step 2: Set Up API Keys

#### Option A: Using .env file (Recommended)

1. Copy the example file:
   ```bash
   copy .env.example .env
   ```

2. Edit `.env` and add your API keys:
   ```bash
   # OpenAI API Key
   OPENAI_API_KEY=sk-your-key-here

   # Blockchain Explorer API Keys
   ETHERSCAN_API_KEY=your-etherscan-key
   BASESCAN_API_KEY=your-basescan-key
   POLYGONSCAN_API_KEY=your-polygon-key
   # ... add others as needed
   ```

#### Option B: Using settings.yaml

Edit `config/settings.yaml`:
```yaml
openai_api_key: "sk-your-key-here"

api_keys:
  ethereum: "your-etherscan-key"
  base: "your-basescan-key"
  polygon: "your-polygon-key"
  # ... add others as needed
```

## API Keys - Where to Get Them

### OpenAI API Key
- **Required for**: LLM-based vulnerability analysis
- **Get it from**: https://platform.openai.com/api-keys
- **Free tier**: No, paid service
- **Environment variable**: `OPENAI_API_KEY`

### Blockchain Explorer API Keys

All blockchain explorers offer free API keys with rate limits:

#### Ethereum (Etherscan)
- **URL**: https://etherscan.io/myapikey
- **Variable**: `ETHERSCAN_API_KEY`
- **Free tier**: Yes (5 calls/second)

#### Base (BaseScan)
- **URL**: https://basescan.org/myapikey
- **Variable**: `BASESCAN_API_KEY`
- **Free tier**: Yes

#### Polygon (PolygonScan)
- **URL**: https://polygonscan.com/myapikey
- **Variable**: `POLYGONSCAN_API_KEY`
- **Free tier**: Yes

#### BSC (BscScan)
- **URL**: https://bscscan.com/myapikey
- **Variable**: `BSCSCAN_API_KEY`
- **Free tier**: Yes

#### Arbitrum (Arbiscan)
- **URL**: https://arbiscan.io/myapikey
- **Variable**: `ARBISCAN_API_KEY`
- **Free tier**: Yes

#### Optimism
- **URL**: https://optimistic.etherscan.io/myapikey
- **Variable**: `OPTIMISM_API_KEY`
- **Free tier**: Yes

#### Avalanche (SnowTrace)
- **URL**: https://snowtrace.io/myapikey
- **Variable**: `SNOWTRACE_API_KEY`
- **Free tier**: Yes

#### Fantom (FTMScan)
- **URL**: https://ftmscan.com/myapikey
- **Variable**: `FTMSCAN_API_KEY`
- **Free tier**: Yes

## Configuration Options

### LLM Settings

```yaml
llm:
  model: "gpt-4"           # Model: gpt-4, gpt-3.5-turbo, etc.
  temperature: 0.1         # 0.0 = deterministic, 2.0 = creative
  max_tokens: 4000         # Maximum response length
```

### Analysis Settings

```yaml
analysis:
  max_time: 300            # Maximum analysis time (seconds)
  detailed_logging: true   # Enable detailed logs
```

### Report Settings

```yaml
report:
  format: "html"           # Format: html, json, markdown
  include_poc: true        # Include proof-of-concept code
```

## Using the Configuration

### In the Web UI
- API keys configured in `.env` or `settings.yaml` are automatically used
- You can still override them by providing a key in the web interface

### In Python Scripts
```python
from src.config import config

# Get OpenAI key
openai_key = config.get_openai_key()

# Get blockchain API key
eth_key = config.get_api_key('ethereum')

# Get LLM configuration
llm_config = config.get_llm_config()
```

## Security Best Practices

1. **Never commit `.env` to version control**
   - `.env` is already in `.gitignore`
   - Use `.env.example` as a template

2. **Protect your API keys**
   - Don't share them publicly
   - Rotate them if exposed

3. **Use environment-specific configs**
   - Development: `.env.development`
   - Production: `.env.production`

## Troubleshooting

### API Key Not Working
1. Check if the key is properly set in `.env` or `settings.yaml`
2. Verify no extra spaces or quotes in the configuration
3. Restart the application after changing configuration

### "Module 'config' not found"
- Make sure you're running from the project root directory
- Check that `src/config.py` exists

### Rate Limit Errors
- Blockchain explorer free tiers have rate limits (usually 5 calls/second)
- Consider upgrading to a paid plan for heavy usage

## Example Complete Configuration

**.env file:**
```bash
# Core API Keys
OPENAI_API_KEY=sk-proj-abcdefghijklmnop...

# Blockchain Explorers
ETHERSCAN_API_KEY=ABC123DEF456...
BASESCAN_API_KEY=GHI789JKL012...
POLYGONSCAN_API_KEY=MNO345PQR678...

# Optional Settings
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.1
MAX_ANALYSIS_TIME=300
```

**config/settings.yaml:**
```yaml
openai_api_key: "sk-proj-abcdefghijklmnop..."

api_keys:
  ethereum: "ABC123DEF456..."
  base: "GHI789JKL012..."
  polygon: "MNO345PQR678..."

llm:
  model: "gpt-4"
  temperature: 0.1
  max_tokens: 4000

analysis:
  max_time: 300
  detailed_logging: true

report:
  format: "html"
  include_poc: true
```
