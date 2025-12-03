from celery import Celery
import asyncio
import os
from llm_service import LLMService
from slither_wrapper import SlitherWrapper
import logging

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Initialize Celery
app = Celery('web3_hunter', broker=REDIS_URL, backend=REDIS_URL)

# Initialize Services
# Note: Celery workers fork, so we initialize inside the task or use a global lazy init
llm_service = None
slither = SlitherWrapper()

def get_llm_service():
    global llm_service
    if llm_service is None:
        llm_service = LLMService()
    return llm_service

@app.task
def scan_contract(source_code: str, file_path: str = "temp_contract.sol"):
    """
    Celery task to scan a contract.
    1. Save source to file.
    2. Run Slither.
    3. Run LLM Analysis (with Slither context).
    4. Return combined report.
    """
    logger = logging.getLogger("CeleryWorker")
    logger.info(f"Scanning contract...")

    # Save source code to a temp file for Slither
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(source_code)

    # Run Slither
    slither_findings = slither.run(file_path)
    logger.info(f"Slither found {len(slither_findings)} issues.")

    # Run LLM Analysis
    # We need to run async code in sync Celery task
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    service = get_llm_service()
    
    # Enhance prompt with Slither findings
    slither_context = f"\nSlither Findings: {slither_findings}\n"
    
    # We might want to pass this context to the LLM. 
    # The current LLMService.analyze_code just takes source_code.
    # We can append the context to the source code or modify LLMService.
    # For now, appending to source code as a comment or separate section in the prompt.
    
    full_prompt_content = f"{source_code}\n\n/*\n{slither_context}\n*/"
    
    llm_result = loop.run_until_complete(service.analyze_code(full_prompt_content))
    
    # Combine results
    report = {
        "slither": slither_findings,
        "llm": llm_result
    }
    
    return report
