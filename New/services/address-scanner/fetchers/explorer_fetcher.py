"""
Explorer Fetcher Module

Fetches verified source code from various blockchain explorers
"""

import httpx
import os
from typing import Optional, Dict
from enum import Enum

class Chain(str, Enum):
    """Supported blockchain networks"""
    ETHEREUM = "ethereum"
    BSC = "bsc"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    BASE = "base"



class ExplorerFetcher:
    """
    Fetch verified source code from block explorers
    
    Supports:
    - Etherscan (Ethereum)
    - BSCScan (Binance Smart Chain)
    - PolygonScan (Polygon)
    - Arbiscan (Arbitrum)
    - Optimistic Etherscan (Optimism)
    """
    
    EXPLORER_APIS = {
        Chain.ETHEREUM: "https://api.etherscan.io/api",
        Chain.BSC: "https://api.bscscan.com/api",
        Chain.POLYGON: "https://api.polygonscan.com/api",
        Chain.ARBITRUM: "https://api.arbiscan.io/api",
        Chain.OPTIMISM: "https://api-optimistic.etherscan.io/api",
        Chain.BASE: "https://api.basescan.org/api",
    }
    
    # Get API keys from environment variables
    API_KEYS = {
        Chain.ETHEREUM: os.getenv("ETHERSCAN_API_KEY", ""),
        Chain.BSC: os.getenv("BSCSCAN_API_KEY", ""),
        Chain.POLYGON: os.getenv("POLYGONSCAN_API_KEY", ""),
        Chain.ARBITRUM: os.getenv("ARBISCAN_API_KEY", ""),
        Chain.OPTIMISM: os.getenv("OPTIMISM_API_KEY", ""),
        Chain.BASE: os.getenv("BASESCAN_API_KEY", ""),
    }
    
    @classmethod
    async def fetch_source(cls, address: str, chain: Chain) -> Optional[Dict]:
        """
        Fetch verified source code from block explorer
        
        Args:
            address: Contract address
            chain: Blockchain network
            
        Returns:
            Dict containing:
            - source_code: Full contract source code
            - abi: Contract ABI
            - contract_name: Name of the contract
            - compiler_version: Solidity compiler version
            - optimization_used: Whether optimization was enabled
            - runs: Optimization runs
            None if not found or not supported
        """
        if chain not in cls.EXPLORER_APIS:
            return None
        
        params = {
            'module': 'contract',
            'action': 'getsourcecode',
            'address': address,
            'apikey': cls.API_KEYS.get(chain, '')
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    cls.EXPLORER_APIS[chain],
                    params=params,
                    timeout=15.0
                )
                
                if response.status_code != 200:
                    print(f"Explorer API returned {response.status_code}")
                    return None
                
                data = response.json()
                
                # Check if request was successful
                if data.get('status') != '1':
                    print(f"Explorer API error: {data.get('message', 'Unknown error')}")
                    return None
                
                if not data.get('result'):
                    return None
                
                result = data['result'][0]
                source_code = result.get('SourceCode')
                
                # Check if source code exists and is not empty
                if not source_code or source_code == '':
                    return None
                
                return {
                    'source_code': source_code,
                    'abi': result.get('ABI', ''),
                    'contract_name': result.get('ContractName', 'Unknown'),
                    'compiler_version': result.get('CompilerVersion', ''),
                    'optimization_used': result.get('OptimizationUsed', '0'),
                    'runs': result.get('Runs', '200'),
                    'constructor_args': result.get('ConstructorArguments', ''),
                    'license_type': result.get('LicenseType', '')
                }
                
            except httpx.TimeoutException:
                print(f"Timeout fetching from {chain.value} explorer")
                return None
            except httpx.ConnectError:
                print(f"Connection error to {chain.value} explorer")
                return None
            except Exception as e:
                print(f"Error fetching from explorer: {e}")
                return None
    
    @classmethod
    async def verify_address_exists(cls, address: str, chain: Chain) -> bool:
        """
        Verify if an address exists on the blockchain
        
        Args:
            address: Contract address
            chain: Blockchain network
            
        Returns:
            True if address exists, False otherwise
        """
        if chain not in cls.EXPLORER_APIS:
            return False
        
        params = {
            'module': 'account',
            'action': 'balance',
            'address': address,
            'tag': 'latest',
            'apikey': cls.API_KEYS.get(chain, '')
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    cls.EXPLORER_APIS[chain],
                    params=params,
                    timeout=10.0
                )
                data = response.json()
                return data.get('status') == '1'
            except Exception:
                return False
    
    @classmethod
    def get_explorer_url(cls, address: str, chain: Chain) -> str:
        """
        Get the block explorer URL for an address
        
        Args:
            address: Contract address
            chain: Blockchain network
            
        Returns:
            Full URL to view the contract on the explorer
        """
        explorer_urls = {
            Chain.ETHEREUM: f"https://etherscan.io/address/{address}",
            Chain.BSC: f"https://bscscan.com/address/{address}",
            Chain.POLYGON: f"https://polygonscan.com/address/{address}",
            Chain.ARBITRUM: f"https://arbiscan.io/address/{address}",
            Chain.OPTIMISM: f"https://optimistic.etherscan.io/address/{address}",
            Chain.BASE: f"https://basescan.org/address/{address}",
        }
        
        return explorer_urls.get(chain, f"https://etherscan.io/address/{address}")
