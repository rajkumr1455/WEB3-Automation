from flask import Flask, render_template, request, jsonify
import os
import sys
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tasks import scan_contract, app as celery_app

app = Flask(__name__)

# Store recent scans in memory (for demo; use DB in production)
recent_scans = []

@app.route('/')
def index():
    # Update scan statuses with actual task states
    for scan in recent_scans[:10]:
        if scan['status'] == 'pending':
            task_result = celery_app.AsyncResult(scan['id'])
            if task_result.ready():
                scan['status'] = 'completed'
                scan['result'] = task_result.result
            elif task_result.failed():
                scan['status'] = 'failed'
    
    return render_template('dashboard.html', scans=recent_scans[:10])

@app.route('/api/scan', methods=['POST'])
def trigger_scan():
    """Trigger a new scan via API"""
    data = request.json
    source_code = data.get('source_code')
    contract_name = data.get('name', 'Unnamed')
    
    if not source_code:
        return jsonify({'error': 'No source code provided'}), 400
    
    # Trigger Celery task
    task = scan_contract.delay(source_code)
    
    scan_record = {
        'id': task.id,
        'name': contract_name,
        'timestamp': datetime.now().isoformat(),
        'status': 'pending'
    }
    recent_scans.insert(0, scan_record)
    
    return jsonify({'task_id': task.id, 'status': 'queued'})

@app.route('/api/scan_address', methods=['POST'])
def trigger_address_scan():
    """Trigger a contract scan by address (multi-chain)"""
    data = request.json
    chain = data.get('chain', 'eth')
    contract_address = data.get('address')
    api_key = data.get('api_key', '')
    
    if not contract_address:
        return jsonify({'error': 'No contract address provided'}), 400
    
    # Import and run multi-chain scanner
    import asyncio
    from multichain_scanner import MultiChainScanner
    
    async def run_scan():
        scanner = MultiChainScanner(chain=chain, api_key=api_key)
        return await scanner.scan_address(contract_address)
    
    # Run in thread pool since Flask is sync
    from concurrent.futures import ThreadPoolExecutor
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(lambda: asyncio.run(run_scan()))
    
    # Return immediately
    return jsonify({
        'status': 'processing',
        'chain': chain,
        'address': contract_address,
        'message': f'Scan initiated on {chain.upper()}. Check back in 30-60 seconds.'
    })



@app.route('/api/result/<task_id>')
def get_result(task_id):
    """Get scan result by task ID"""
    task_result = celery_app.AsyncResult(task_id)
    
    if task_result.ready():
        result = task_result.result
        return jsonify({
            'status': 'completed',
            'result': result
        })
    else:
        return jsonify({
            'status': 'pending',
            'state': task_result.state
        })

@app.route('/api/stats')
def get_stats():
    """Get system statistics"""
    from celery import current_app as celery_app
    
    # Get worker stats
    inspect = celery_app.control.inspect()
    stats = inspect.stats()
    
    return jsonify({
        'total_scans': len(recent_scans),
        'workers': stats if stats else {},
        'queue_size': 0  # Placeholder
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
