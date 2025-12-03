from src.orchestration.hunter_graph import HunterGraph

print("Testing HunterGraph with file path...")
graph = HunterGraph()

state = {
    'target_url': 'test',
    'local_path': 'data/uploads/TestContract.sol'
}

print("Running analysis...")
result = graph.analyze_node(state)

print(f"SUCCESS!")
print(f"  Slither issues: {len(result.get('slither_results', []))}")
print(f"  Vulnerabilities: {len(result.get('vulnerabilities', ''))} chars")
print(f"  Code: {len(result.get('flattened_code', ''))} chars")
