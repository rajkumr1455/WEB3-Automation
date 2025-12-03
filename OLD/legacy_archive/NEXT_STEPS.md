# Remaining Manual Setup Steps

## Status Summary
✅ **Complete:**
- Python 3.11.9
- All Python dependencies (9/9)
- Slither (accessible via `python -m slither`)
- Solidity compiler (0.8.20)

⚠️ **Pending:**
- Mythril (optional - symbolic execution)
- Foundry (required - for PoC testing)
- Ollama (required - GPU-accelerated LLM)

---

## 1. Install Mythril (Optional)

Mythril requires special setup on Windows.

```powershell
# Install Mythril
pip install mythril

# Verify installation
python -m mythril version
```

If you encounter issues, Mythril can be skipped for now. The system will work with Slither alone.

---

## 2. Install Foundry (Required)

**Option A: Pre-built binaries (Recommended)**

1. Download latest release from:
   https://github.com/foundry-rs/foundry/releases

2. Look for `foundry_nightly_windows_amd64.zip` or similar

3. Extract to `C:\Program Files\Foundry`

4. Add to PATH:
   - Open: System Properties → Environment Variables
   - Edit PATH → Add: `C:\Program Files\Foundry\bin`

5. Verify:
   ```powershell
   forge --version
   ```

**Option B: Install via Cargo (if you have Rust)**

```powershell
cargo install --git https://github.com/foundry-rs/foundry --profile release --locked foundry-cli anvil chisel
```

---

## 3. Install Ollama (Required for GPU)

**This is the main reason you moved to Windows - GPU acceleration!**

### Installation

1. Download: https://ollama.ai/download/windows

2. Run the installer

3. Verify Ollama is running:
   ```powershell
   ollama --version
   ```

### Pull LLM Model

```powershell
# Start Ollama service (usually auto-starts)
ollama serve

# Pull model for code analysis
ollama pull codellama:13b

# Verify
ollama list
```

### GPU Verification

1. Open **Task Manager** (Ctrl+Shift+Esc)
2. Go to **Performance** tab → **GPU**
3. Test Ollama:
   ```powershell
   ollama run codellama:13b "Explain what a reentrancy attack is"
   ```
4. Watch GPU usage spike during inference

---

## 4. Alternative: Use OpenAI API

If you don't want to install Ollama, you can use OpenAI's API:

1. Create `.env` file in project root:
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

---

## 5. Verify Final Setup

After installing the above, run:

```powershell
python validate_env.py
```

You should see:
- Python Dependencies: 9/9 ✅
- CLI Tools: 2-4/4 (depending on what you installed)
- LLM Backend: OK ✅

---

## Quick Start After Setup

```powershell
# Test with a sample repository
python main.py https://github.com/your-vulnerable-contract-repo
```

---

## Notes on Tool Access

Since the tools aren't on PATH globally, you can:

**Option 1**: Use `python -m` prefix:
```powershell
python -m slither contract.sol
python -m mythril analyze contract.sol
```

**Option 2**: Add Scripts folder to PATH manually:
```
C:\Users\patel\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\local-packages\Python311\Scripts
```

---

## Next Steps After Installation

1. **Test Individual Tools**: Verify each tool works on a sample contract
2. **Complete Missing Implementations**: Follow the implementation plan to finish incomplete features
3. **Run End-to-End Test**: Test the full workflow on a known vulnerable contract

See `implementation_plan.md` for detailed development roadmap.
