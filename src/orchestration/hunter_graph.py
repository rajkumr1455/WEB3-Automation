from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END
from src.ingestion.contract_fetcher import ContractFetcher
from src.ingestion.flattener import SolidityFlattener
from src.ingestion.surya_runner import SuryaRunner
from src.analysis.slither_runner import SlitherRunner
from src.analysis.mythril_runner import MythrilRunner
from src.analysis.llm_auditor import LLMAuditor
from src.knowledge.vector_store import VectorStore
from src.verification.poc_generator import PoCGenerator
from src.verification.foundry_runner import FoundryRunner
from src.detectors.advanced_detectors import advanced_detector
import logging
import json
import os

logger = logging.getLogger(__name__)

class HunterState(TypedDict):
    target_url: str
    local_path: str
    flattened_code: str
    graph_path: str
    slither_results: List[Dict[str, Any]]
    mythril_results: List[Dict[str, Any]]
    vulnerabilities: str # JSON string from LLM
    poc_code: str
    is_verified: bool
    report: str

class HunterGraph:
    def __init__(self):
        self.fetcher = ContractFetcher()
        self.flattener = SolidityFlattener()
        self.surya = SuryaRunner()
        self.slither = SlitherRunner()
        self.mythril = MythrilRunner()
        self.vector_store = VectorStore()
        self.auditor = LLMAuditor()
        self.poc_gen = PoCGenerator()
        self.foundry = FoundryRunner()

    def fetch_node(self, state: HunterState):
        logger.info("Step: Fetching Contract")
        path = self.fetcher.fetch_from_git(state["target_url"])
        
        # Generate Call Graph
        # graph = self.surya.generate_graph(path, "data/graphs")
        graph = ""
        
        return {"local_path": path, "graph_path": graph}

    def analyze_node(self, state: HunterState):
        logger.info("Step: Analyzing Contract")
        
        # Handle both file and directory paths
        local_path = state["local_path"]
        
        if os.path.isfile(local_path):
            # It's a file - use it directly
            main_contract = local_path
            contract_dir = os.path.dirname(local_path)
            logger.info(f"Using provided contract file: {main_contract}")
        else:
            # It's a directory - find main contract
            main_contract = self.flattener.get_main_contract(local_path)
            contract_dir = local_path
            if not main_contract:
                logger.warning("No Solidity contracts found in repository.")
                return {"vulnerabilities": "No contracts found."}
            logger.info(f"Identified main contract: {main_contract}")

        # Flatten the contract
        flattened_path = self.flattener.flatten(main_contract, "data/flattened")
        flattened_code = ""
        if flattened_path and os.path.exists(flattened_path):
            with open(flattened_path, 'r', encoding='utf-8') as f:
                flattened_code = f.read()
        else:
            logger.warning("Flattening failed, using original source.")
            with open(main_contract, 'r', encoding='utf-8') as f:
                flattened_code = f.read()
        
        # Run Slither on the contract file (not directory!)
        logger.info(f"Running Slither on: {main_contract}")
        slither_results = self.slither.run(main_contract)
        logger.info(f"Slither found {len(slither_results)} issues")
        
        # Run Advanced Detectors (2025 threats + missing vulnerabilities)
        advanced_results = advanced_detector.analyze(flattened_code)
        logger.info(f"Advanced detectors found {len(advanced_results)} additional issues")
        
        # Combine Slither and Advanced results
        all_findings = slither_results + advanced_results
        
        # Generate Call Graph (Replacement for Surya)
        call_graph_path = self.slither.generate_call_graph(contract_dir)
        call_graph_dot = ""
        if call_graph_path and os.path.exists(call_graph_path):
            with open(call_graph_path, 'r', encoding='utf-8') as f:
                call_graph_dot = f.read()
        
        # Run Mythril (Placeholder for next phase)
        # mythril_res = self.mythril.run(main_contract)
        mythril_res = []
        
        # Retrieve Context (RAG)
        context = self.vector_store.query(flattened_code)
        
        # Run LLM
        # Pass call graph info if available (append to code or context)
        analysis_content = flattened_code
        if call_graph_dot:
            analysis_content += "\n\n/* CALL GRAPH (DOT FORMAT) */\n" + call_graph_dot
            
        logger.info("Running LLM analysis (this may take a minute)...")
        vulns = self.auditor.analyze(analysis_content, all_findings, context)
        logger.info("LLM analysis completed")
        
        return {
            "slither_results": all_findings, 
            "mythril_results": mythril_res, 
            "vulnerabilities": vulns,
            "flattened_code": flattened_code,
            "call_graph": call_graph_dot
        }

    def verify_node(self, state: HunterState):
        logger.info("Step: Verifying Vulnerabilities")
        vulns = state["vulnerabilities"]
        # If LLM found nothing, skip
        if "[]" in vulns or "No issues" in vulns:
            return {"is_verified": False, "report": "No vulnerabilities found."}

        # Generate PoC for the first vuln (Simplified)
        poc_code = self.poc_gen.generate_exploit(state.get("flattened_code", ""), vulns)
        
        # Write PoC to file
        test_dir = os.path.join(state["local_path"], "test")
        os.makedirs(test_dir, exist_ok=True)
        test_path = os.path.join(test_dir, "Exploit.t.sol")
        
        with open(test_path, "w", encoding="utf-8") as f:
            f.write(poc_code)
            
        logger.info(f"PoC generated at: {test_path}")

        # Run the test
        is_verified = self.foundry.run_test(test_path, state["local_path"])
        
        report = "Vulnerability Verified!" if is_verified else "PoC Failed to Verify."
        
        return {"poc_code": poc_code, "is_verified": is_verified, "report": report}

    def build(self):
        workflow = StateGraph(HunterState)
        
        workflow.add_node("fetch", self.fetch_node)
        workflow.add_node("analyze", self.analyze_node)
        workflow.add_node("verify", self.verify_node)

        workflow.set_entry_point("fetch")
        workflow.add_edge("fetch", "analyze")
        workflow.add_edge("analyze", "verify")
        workflow.add_edge("verify", END)

        return workflow.compile()
