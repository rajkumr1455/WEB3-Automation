import argparse
import logging
import sys
from src.orchestration.hunter_graph import HunterGraph

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("main")

def main():
    parser = argparse.ArgumentParser(description="Web3 Hunter - Automated Bug Bounty System")
    parser.add_argument("url", help="Target Git Repository URL")
    args = parser.parse_args()

    logger.info(f"Starting Hunter against target: {args.url}")

    try:
        hunter = HunterGraph()
        workflow = hunter.build()
        
        # Initial state
        initial_state = {
            "target_url": args.url,
            "local_path": "",
            "flattened_code": "",
            "graph_path": "",
            "slither_results": [],
            "mythril_results": [],
            "vulnerabilities": "",
            "poc_code": "",
            "is_verified": False,
            "report": ""
        }

        # Run the workflow
        final_state = workflow.invoke(initial_state)
        
        print("\n" + "="*50)
        print("HUNTER REPORT")
        print("="*50)
        print(f"Target: {args.url}")
        print(f"Local Path: {final_state.get('local_path')}")
        print(f"Call Graph: {final_state.get('graph_path')}")
        print("-" * 20)
        print("Vulnerabilities Found:")
        print(final_state.get("vulnerabilities"))
        print("-" * 20)
        if final_state.get("poc_code"):
            print("PoC Generated:")
            print(final_state.get("poc_code"))
        else:
            print("No PoC generated.")
        print("="*50 + "\n")

    except Exception as e:
        logger.critical(f"System failure: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
