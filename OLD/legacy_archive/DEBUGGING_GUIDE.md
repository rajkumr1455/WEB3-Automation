# Web3 Hunter - End-to-End Testing & Debugging Guide

## Problem Identified: Scans Stuck at 10%

### Root Cause Analysis

The scanning process gets stuck at 10% because:

1. **HunterGraph Initialization Fails** - The `HunterGraph()` class requires:
   - Ollama running locally at `http://localhost:11434`
   - LLM model (codellama:13b or similar) downloaded
   - OpenAI API key (if using ChatGPT instead of Ollama)

2. **Missing Dependencies** - Several tools need to be available:
   - Slither (Python package)
   - Foundry/Forge (for verification)
   - Git (for GitHub scanning)

3. **Silent Failures** - Errors weren't being logged properly

### Immediate Solutions

####  **Option 1: Quick Fix - Mock Mode (Testing Only)**

Create a simplified scanner that doesn't require LLM:

```python
# In web_ui/app.py, add a simple mock scanner
def run_scan_simple(scan_id, filepath, filename):
    """Simplified scan without LLM for testing"""
    try:
        scan_results[scan_id]['progress'] = 20
        
        # Just run Slither
        from src.analysis.slither_runner import SlitherRunner
        slither = SlitherRunner()
        
        scan_results[scan_id]['progress'] = 50
        directory = os.path.dirname(filepath)
        slither_results = slither.run(directory)
        
        scan_results[scan_id]['progress'] = 80
        
        # Generate simple report
        from src.reporting.report_generator import ReportGenerator
        report_gen = ReportGenerator()
        
        with open(filepath, 'r') as f:
            source_code = f.read()
        
        report_path = report_gen.generate_html_report(
            contract_name=Path(filename).stem,
            source_code=source_code,
            findings="{}",  # No LLM findings
            slither_results=slither_results,
            poc_code=''
        )
        
        scan_results[scan_id]['progress'] = 100
        scan_results[scan_id]['status'] = 'completed'
        scan_results[scan_id]['report_url'] = f"/reports/{Path(report_path).name}"
        scan_results[scan_id]['slither_issues'] = len(slither_results)
        scan_results[scan_id]['vulnerabilities_found'] = 0  # LLM disabled
        
    except Exception as e:
        logger.error(f"Scan failed: {e}", exc_info=True)
        scan_results[scan_id]['status'] = 'failed'
        scan_results[scan_id]['error'] = str(e)
```

#### **Option 2: Fix LLM Configuration**

1. **Check if Ollama is running**:
   ```bash
   # Test Ollama
   curl http://localhost:11434/api/tags
   ```

2. **Or configure OpenAI instead**:
   ```yaml
   # In config/settings.yaml
   llm:
     provider: "openai"  # Change from "ollama"
     model: "gpt-4"
     temperature: 0.1
   ```

3. **Add your OpenAI key to `.env`**:
   ```bash
   OPENAI_API_KEY=sk-your-key-here
   ```

#### **Option 3: Add Better Error Logging** (RECOMMENDED FIRST STEP)

The corrupted app.py needs to be fixed. Here's the correct structure:

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_scan(scan_id, filepath, filename):
    """Background scan task with detailed logging"""
    try:
        logger.info(f"[{scan_id}] Starting scan for {filename}")
        scan_results[scan_id]['progress'] = 10
        
        # Initialize components
        logger.info(f"[{scan_id}] Initializing HunterGraph...")
        graph = HunterGraph()
        logger.info(f"[{scan_id}] HunterGraph initialized")
        
        report_gen = ReportGenerator()
        scan_results[scan_id]['progress'] = 30
        
        # Run scan...
        logger.info(f"[{scan_id}] Running analysis...")
        state = {
            "target_url": f"upload://{filename}",
            "local_path": os.path.dirname(filepath),
            "slither_results": [],
            "flattened_code": "",
            "vulnerabilities": ""
        }
        
        result = graph.analyze_node(state)
        scan_results[scan_id]['progress'] = 70
        
        # Rest of the code...
        
    except Exception as e:
        logger.error(f"[{scan_id}] SCAN FAILED: {str(e)}", exc_info=True)
        scan_results[scan_id]['status'] = 'failed'
        scan_results[scan_id]['error'] = str(e)
        scan_results[scan_id]['progress'] = 0
```

### Testing Steps

1. **Fix the corrupted app.py** - It currently has indentation errors
2. **Add logging configuration** - So we can see what's failing
3. **Test with a simple .sol file**
4. **Check the terminal output** for error messages
5. **Verify dependencies are installed**:
   ```bash
   slither --version
   forge --version
   ollama list  # or check OpenAI key
   ```

### Next Steps

1. I need to **rewrite app.py** properly (it's currently corrupted)
2. Add **proper logging** throughout
3. Create a **simplified test mode** that doesn't require LLM
4. Test end-to-end with a sample contract

Would you like me to:
- A) Fix the corrupted app.py file first
- B) Create a simplified test-mode scanner
- C) Help configure Ollama/OpenAI properly
