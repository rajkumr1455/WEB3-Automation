# Windows Setup Guide - Web3 Hunter

This guide helps you set up the Web3 Hunter bug bounty automation system on Windows.

## Quick Start

### 1. Install Dependencies

```powershell
# Navigate to project directory
cd c:\Users\patel\Desktop\web3_hunter

# Activate virtual environment (if not already active)
.\venv\Scripts\Activate.ps1

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Install Blockchain Tools

#### Solidity Compiler
```powershell
pip install solc-select
solc-select install 0.8.20
solc-select use 0.8.20
```

#### Slither (Already in requirements.txt)
```powershell
# Verify installation
slither --version
```

#### Mythril
```powershell
pip install mythril
myth version
```

#### Foundry
1. Download from: https://github.com/foundry-rs/foundry/releases
2. Extract to `C:\Program Files\Foundry`
3. Add to PATH:
   ```powershell
   $env:Path += ";C:\Program Files\Foundry\bin"
   # Or add permanently via System Environment Variables
   ```
4. Verify:
   ```powershell
   forge --version
   ```

### 3. Configure LLM Backend

#### Option A: Ollama (GPU Accelerated)
1. Download: https://ollama.ai/download/windows
2. Install and start Ollama service
3. Pull model:
   ```powershell
   ollama pull codellama:13b
   # Or for faster inference:
   ollama pull llama2:7b
   ```
4. Verify GPU usage in Task Manager

#### Option B: OpenAI API
1. Create `.env` file:
   ```
   OPENAI_API_KEY=sk-your-key-here
   ```
2. Update `config/settings.yaml`:
   ```yaml
   llm:
     provider: "openai"
     model: "gpt-4"
     temperature: 0.1
   ```

### 4. Test Installation

```powershell
# Test with a sample repository
python main.py https://github.com/your-test-repo
```

## GPU Acceleration Verification

### Check GPU Usage
1. Open Task Manager (Ctrl+Shift+Esc)
2. Go to Performance tab → GPU
3. Run a test inference with Ollama
4. Monitor GPU usage (should show activity)

### Optimize for GPU
```powershell
# For Ollama, enable GPU layers
ollama run codellama:13b --gpu-layers 35
```

## Troubleshooting

### Issue: Slither not finding contracts
**Solution:** Ensure solc is in PATH and correct version is selected

### Issue: Mythril timeout
**Solution:** Increase timeout in `config/settings.yaml`:
```yaml
mythril:
  timeout: 600
```

### Issue: Foundry not found
**Solution:** Add Foundry to PATH manually or install via Chocolatey:
```powershell
choco install foundry
```

### Issue: Ollama not using GPU
**Solution:** 
- Update GPU drivers
- Restart Ollama service
- Check: https://ollama.ai/docs/gpu

## Project Structure

```
web3_hunter/
├── config/
│   └── settings.yaml       # Main configuration
├── data/                   # Data storage
│   └── vector_db/         # RAG database
├── src/
│   ├── analysis/          # Slither, Mythril, LLM
│   ├── ingestion/         # Git fetch, flattening
│   ├── knowledge/         # Vector store
│   ├── orchestration/     # LangGraph workflow
│   └── verification/      # PoC generation, Foundry
├── tests/                 # Unit tests
├── main.py               # Entry point
└── requirements.txt      # Python dependencies
```

## Next Steps

1. Review `implementation_plan.md` for development roadmap
2. Test individual components
3. Run end-to-end workflow on sample contracts
4. Configure alerts and reporting

## Resources

- **Slither:** https://github.com/crytic/slither
- **Mythril:** https://github.com/ConsenSys/mythril
- **Foundry:** https://book.getfoundry.sh/
- **LangGraph:** https://langchain-ai.github.io/langgraph/
- **Ollama:** https://ollama.ai/
