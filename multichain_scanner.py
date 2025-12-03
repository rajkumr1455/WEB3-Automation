import httpx
import asyncio
import os
from typing import Optional, Dict, Tuple
from unified_scanner import UnifiedScanner

class MultiChainScanner:
    """
    Multi-chain contract scanner supporting multiple EVM chains
    Uses Etherscan-compatible APIs
    """
    
    CHAIN_CONFIG = {
        'eth': {
            'name': 'Ethereum',
            'api_url': 'https://api.etherscan.io/api',
            'default_key': 'YourApiKeyToken'
        },
        'bsc': {
            'name': 'Binance Smart Chain',
            'api_url': 'https://api.bscscan.com/api',
            'default_key': 'YourApiKeyToken'
        },
        'polygon': {
            'name': 'Polygon',
            'api_url': 'https://api.polygonscan.com/api',
            'default_key': 'YourApiKeyToken'
        },
        'arbitrum': {
            'name': 'Arbitrum',
            'api_url': 'https://api.arbiscan.io/api',
            'default_key': 'YourApiKeyToken'
        },
        'optimism': {
            'name': 'Optimism',
            'api_url': 'https://api-optimistic.etherscan.io/api',
            'default_key': 'YourApiKeyToken'
        }
    }
    
    def __init__(self, chain: str = 'eth', api_key: Optional[str] = None):
        if chain not in self.CHAIN_CONFIG:
            raise ValueError(f"Unsupported chain: {chain}")
        
        self.chain = chain
        self.config = self.CHAIN_CONFIG[chain]
        self.api_key = api_key or os.getenv(f'{chain.upper()}_API_KEY') or self.config['default_key']
        self.scanner = UnifiedScanner(chain=chain)
        
    async def fetch_source(self, contract_address: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Fetch contract source code from blockchain explorer API
        """
        params = {
            "module": "contract",
            "action": "getsourcecode",
            "address": contract_address,
            "apikey": self.api_key
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.config['api_url'], params=params)
                data = response.json()
                
                if data.get('status') == '1' and data.get('result'):
                    result = data['result'][0]
                    source_code = result.get('SourceCode', '')
                    contract_name = result.get('ContractName', 'Unknown')
                    
                    # Handle Etherscan's JSON-encoded source code
                    if source_code.startswith('{{'):
                        # Multi-file source (JSON format)
                        import json
                        try:
                            source_obj = json.loads(source_code[1:-1])
                            # Get main contract file
                            if 'sources' in source_obj:
                                files = source_obj['sources']
                                # Concatenate all files
                                source_code = '\n\n'.join([f"// File: {name}\n{content['content']}" 
                                                          for name, content in files.items()])
                        except:
                            pass
                    
                    return source_code, contract_name
                else:
                    error_msg = data.get('result', 'Unknown error')
                    print(f"[!] API Error: {error_msg}")
                    return None, None
        except Exception as e:
            print(f"[!] Exception fetching source: {e}")
            return None, None
    
    async def scan_address(self, contract_address: str) -> Dict:
        """
        Scan a contract by address
        """
        print(f"[*] Fetching contract from {self.config['name']}: {contract_address}")
        
        source, name = await self.fetch_source(contract_address)
        
        if not source:
            return {
                "error": "Could not fetch contract source. Check address and API key.",
                "chain": self.chain,
                "address": contract_address
            }
        
        if not source.strip():
            return {
                "error": "Contract source code is empty or not verified.",
                "chain": self.chain,
                "address": contract_address
            }
        
        print(f"[+] Found contract: {name}")
        print(f"[+] Source code length: {len(source)} characters")
        
        # Run full scan
        result = await self.scanner.scan_contract(source, name)
        result['chain'] = self.chain
        result['address'] = contract_address
        
        return result

if __name__ == "__main__":
    async def test():
        # Test with BSC contract
        scanner = MultiChainScanner(chain='bsc', api_key='YOUR_API_KEY')
        result = await scanner.scan_address("0x...")
        print(result)
    
    asyncio.run(test())
