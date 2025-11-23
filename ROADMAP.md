# Web3 Hunter - Development Roadmap

## Phase 1: Environment Setup ⚙️

### 1.1 Install Core Tools
- [ ] Install Foundry (forge, cast, anvil)
- [ ] Install solc-select and configure Solidity compiler
- [ ] Verify Slither and Mythril installations
- [ ] Test GPU-accelerated Ollama setup

### 1.2 Verify Dependencies
- [ ] Run `pip install -r requirements.txt`
- [ ] Test Slither on sample contract
- [ ] Test Mythril on sample contract
- [ ] Verify LangGraph workflow initialization

---

## Phase 2: Complete Missing Implementations 🛠️

### 2.1 Ingestion Layer
- [ ] **SolidityFlattener**: Implement contract flattening logic
- [ ] **SuryaRunner**: Enable call graph generation
- [ ] **ContractFetcher**: Add logic to identify main contract files

### 2.2 Analysis Layer
- [ ] **MythrilRunner**: Uncomment and integrate Mythril analysis
- [ ] **LLMAuditor**: Update to accept both Slither + Mythril results
- [ ] **HunterGraph**: Implement proper source code reading logic

### 2.3 Verification Layer
- [ ] **FoundryRunner**: Complete test execution implementation
- [ ] **PoCGenerator**: Enhance exploit generation
- [ ] **HunterGraph**: Integrate verification results into report

---

## Phase 3: Testing & Validation ✅

### 3.1 Unit Tests
- [ ] Test contract fetching from Git
- [ ] Test Slither analysis parsing
- [ ] Test Mythril integration
- [ ] Test LLM auditor responses
- [ ] Test PoC generation

### 3.2 Integration Tests
- [ ] Test end-to-end workflow with DamnVulnerableDeFi contracts
- [ ] Test with real-world vulnerable contracts
- [ ] Validate report generation
- [ ] Test error handling and recovery

### 3.3 Performance Tests
- [ ] Benchmark LLM inference speed (GPU vs CPU)
- [ ] Measure analysis time for different contract sizes
- [ ] Optimize vector store queries
- [ ] Profile memory usage

---

## Phase 4: Enhancement Features 🚀

### 4.1 Advanced Analysis
- [ ] Parallel analysis for multiple contracts
- [ ] Support for additional vulnerability patterns
- [ ] Integration with more security tools (Echidna, Manticore)
- [ ] Custom vulnerability pattern detection

### 4.2 Reporting
- [ ] Generate HTML reports with visualizations
- [ ] Export to PDF format
- [ ] Add vulnerability severity scoring
- [ ] Include remediation suggestions

### 4.3 RAG Improvements
- [ ] Expand vector database with more vulnerability examples
- [ ] Improve context retrieval accuracy
- [ ] Add support for latest Solidity versions
- [ ] Index common DeFi patterns

---

## Quick Reference Commands

### Setup
```powershell
# Install dependencies
pip install -r requirements.txt

# Install Foundry
# Download from: https://getfoundry.sh

# Start Ollama
ollama serve
ollama pull codellama:13b
```

### Development
```powershell
# Run main workflow
python main.py https://github.com/target/repo

# Run tests
python -m pytest tests/

# Check tool versions
slither --version
myth version
forge --version
```

### Testing Sample Contracts
```powershell
# Test with known vulnerable contracts
python main.py https://github.com/OpenZeppelin/damn-vulnerable-defi
```

---

## Current Priority

> Focus on **Phase 1** first to ensure Windows environment is properly configured with GPU acceleration before implementing missing features.

**Next Immediate Actions:**
1. Install Foundry for Windows
2. Configure Ollama with GPU support  
3. Test Slither/Mythril on sample contract
4. Verify LangGraph workflow runs successfully
