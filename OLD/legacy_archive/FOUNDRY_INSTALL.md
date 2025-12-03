# Foundry Installation Options

Since the Foundry repository is cloned but Rust isn't installed, you have two options:

## Option 1: Download Pre-built Binaries (Recommended - Fastest)

1. Visit: https://github.com/foundry-rs/foundry/releases/latest

2. Download **foundry_nightly_windows_amd64.zip** (or latest Windows release)

3. Extract to a location (e.g., `C:\Program Files\Foundry\bin`)

4. Add to PATH:
   - Open: **System Properties** → **Environment Variables**
   - Edit **Path** → Add: `C:\Program Files\Foundry\bin`

5. Restart terminal and verify:
   ```powershell
   forge --version
   cast --version
   anvil --version
   ```

## Option 2: Build from Source (Requires Rust)

If you prefer building from the cloned repo:

1. Install Rust:
   ```powershell
   # Download and run installer from:
   https://rustup.rs
   ```

2. Restart terminal to load Rust

3. Build Foundry:
   ```powershell
   cd foundry
   cargo build --release
   ```

4. Add to PATH:
   ```powershell
   $env:Path += ";$PWD\target\release"
   ```

## Current Status

✅ Foundry repository cloned: `c:\Users\patel\Desktop\web3_hunter\foundry`  
❌ Rust not installed (required for building from source)

**Recommendation**: Use Option 1 (pre-built binaries) for quick setup.

After installation, run:
```powershell
.\setup_session.ps1
```
