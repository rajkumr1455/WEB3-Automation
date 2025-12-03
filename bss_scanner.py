import httpx
import asyncio
from typing import Optional, Dict
from unified_scanner import UnifiedScanner

class BSSScanner:
    """
    Binance Smart Chain contract scanner
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or "YourApiKeyToken"
        self.base_url = "https://api.bscscan.com/api"
        self.scanner = UnifiedScanner(chain="bss")
        
    async def fetch_source(self, contract_address: str) -> Optional[str]:
        """
        Fetch contract source code from BscScan
        """
        params = {
            "module": "contract",
            "action": "getsourcecode",
            "address": contract_address,
            "apikey": self.api_key
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url, params=params)
            data = response.json()
            
            if data['status'] == '1' and data['result']:
                source_code = data['result'][0]['SourceCode']
                contract_name = data['result'][0]['ContractName']
                return source_code, contract_name
        
        return None, None
    
    async def scan_address(self, contract_address: str) -> Dict:
        """
        Scan a BSS contract by address
        """
        print(f"[*] Fetching contract from BSS: {contract_address}")
        
        source, name = await self.fetch_source(contract_address)
        
        if not source:
            return {"error": "Could not fetch contract source"}
        
        print(f"[+] Found contract: {name}")
        return await self.scanner.scan_contract(source, name)

if __name__ == "__main__":
    async def test():
        scanner = BSSScanner()
        # Example BSS contract (replace with actual address)
        result = await scanner.scan_address("0x...")
        print(result)
    
    asyncio.run(test())
