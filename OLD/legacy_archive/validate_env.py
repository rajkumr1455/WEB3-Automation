"""
Environment Validation Script for Web3 Hunter
Tests all dependencies and tools required for Windows development.
"""

import subprocess
import sys
import os
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}[+] {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}[-] {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}[!] {text}{Colors.END}")

def check_command(cmd, name, version_flag="--version"):
    """Check if a command-line tool is installed."""
    try:
        result = subprocess.run(
            [cmd, version_flag],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip().split('\n')[0]
            print_success(f"{name} installed: {version}")
            return True
        else:
            print_error(f"{name} not found or not working properly")
            return False
    except FileNotFoundError:
        print_error(f"{name} not found in PATH")
        return False
    except subprocess.TimeoutExpired:
        print_error(f"{name} command timed out")
        return False
    except Exception as e:
        print_error(f"{name} check failed: {str(e)}")
        return False

def check_python_module(module_name, import_name=None):
    """Check if a Python module is installed."""
    if import_name is None:
        import_name = module_name
    
    try:
        __import__(import_name)
        print_success(f"Python module '{module_name}' installed")
        return True
    except ImportError:
        print_error(f"Python module '{module_name}' not installed")
        return False

def check_ollama():
    """Check if Ollama is running and has models."""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            models = result.stdout.strip().split('\n')[1:]  # Skip header
            if models and models[0]:
                print_success(f"Ollama running with {len(models)} model(s)")
                for model in models[:3]:  # Show first 3 models
                    print(f"  - {model.split()[0]}")
                return True
            else:
                print_warning("Ollama running but no models installed")
                print("  Run: ollama pull codellama:13b")
                return False
        else:
            print_error("Ollama not responding")
            return False
    except FileNotFoundError:
        print_error("Ollama not found - install from https://ollama.ai")
        return False
    except Exception as e:
        print_error(f"Ollama check failed: {str(e)}")
        return False

def check_directory_structure():
    """Verify project directory structure."""
    required_dirs = [
        "src/analysis",
        "src/ingestion",
        "src/knowledge",
        "src/orchestration",
        "src/verification",
        "config",
        "data",
        "tests"
    ]
    
    all_ok = True
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print_success(f"Directory exists: {dir_path}")
        else:
            print_error(f"Directory missing: {dir_path}")
            all_ok = False
    
    return all_ok

def check_gpu_availability():
    """Check if GPU is available for PyTorch/Ollama."""
    print("\n" + Colors.BOLD + "GPU Availability:" + Colors.END)
    
    # Check CUDA
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            print_success(f"CUDA GPU available: {gpu_name}")
            return True
        else:
            print_warning("CUDA GPU not available (CPU mode)")
            return False
    except ImportError:
        print_warning("PyTorch not installed (optional for GPU check)")
        return None

def main():
    print_header("Web3 Hunter - Environment Validation")
    
    results = {
        'python_modules': [],
        'cli_tools': [],
        'optional': []
    }
    
    # Check Python version
    print_header("Python Environment")
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 10):
        print_success(f"Python version: {py_version}")
    else:
        print_error(f"Python {py_version} - requires 3.10+")
    
    # Check Python modules
    print_header("Python Dependencies")
    modules = [
        ('langchain', 'langchain'),
        ('langgraph', 'langgraph'),
        ('langchain-community', 'langchain_community'),
        ('langchain-openai', 'langchain_openai'),
        ('pydantic', 'pydantic'),
        ('requests', 'requests'),
        ('python-dotenv', 'dotenv'),
        ('web3', 'web3'),
        ('slither-analyzer', 'slither'),
    ]
    
    for module, import_name in modules:
        result = check_python_module(module, import_name)
        results['python_modules'].append(result)
    
    # Check CLI Tools
    print_header("Blockchain Security Tools")
    
    tools = [
        ('slither', 'Slither', '--version'),
        ('myth', 'Mythril', 'version'),
        ('forge', 'Foundry (forge)', '--version'),
        ('solc', 'Solidity Compiler', '--version'),
    ]
    
    for cmd, name, flag in tools:
        result = check_command(cmd, name, flag)
        results['cli_tools'].append(result)
    
    # Check Ollama
    print_header("LLM Backend")
    ollama_ok = check_ollama()
    results['optional'].append(ollama_ok)
    
    # Check directory structure
    print_header("Project Structure")
    dir_ok = check_directory_structure()
    
    # Check GPU
    print_header("Hardware Acceleration")
    gpu_ok = check_gpu_availability()
    
    # Summary
    print_header("Summary")
    
    python_score = sum(results['python_modules'])
    python_total = len(results['python_modules'])
    tools_score = sum(results['cli_tools'])
    tools_total = len(results['cli_tools'])
    
    print(f"Python Dependencies: {python_score}/{python_total}")
    print(f"CLI Tools: {tools_score}/{tools_total}")
    print(f"Directory Structure: {'OK' if dir_ok else 'MISSING'}")
    print(f"LLM Backend (Ollama): {'OK' if ollama_ok else 'NOT READY'}")
    
    if gpu_ok:
        print(f"GPU Acceleration: OK")
    elif gpu_ok is False:
        print(f"GPU Acceleration: WARNING (CPU mode)")
    
    print("\n" + Colors.BOLD + "Next Steps:" + Colors.END)
    
    if python_score < python_total:
        print("1. Install missing Python dependencies:")
        print("   pip install -r requirements.txt")
    
    if tools_score < tools_total:
        print("2. Install missing tools (see WINDOWS_SETUP.md)")
    
    if not ollama_ok:
        print("3. Setup Ollama:")
        print("   - Download: https://ollama.ai/download/windows")
        print("   - Run: ollama pull codellama:13b")
    
    if python_score == python_total and tools_score == tools_total and ollama_ok:
        print_success("\nAll systems ready! You can start using Web3 Hunter.")
        print("\nRun: python main.py <git-repo-url>")
    
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()
