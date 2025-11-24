import requests
import logging
from typing import Dict, Any, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.config import config

logger = logging.getLogger(__name__)

class EtherscanAPI:
    """
    Multi-chain block explorer API integration.
    Supports: Ethereum, Base, Polygon, BSC, Arbitrum, Optimism
    """
    
    # Block Explorer API endpoints
    EXPLORERS = {
        "ethereum": {
            "url": "https://api.etherscan.io/api",
            "name": "Etherscan"
        },
        "base": {
            "url": "https://api.basescan.org/api",
            "name": "BaseScan"
        },
        "polygon": {
            "url": "https://api.polygonscan.com/api",
            "name": "PolygonScan"
        },
        "bsc": {
            "url": "https://api.bscscan.com/api",
            "name": "BscScan"
        },
        "arbitrum": {
            "url": "https://api.arbiscan.io/api",
            "name": "Arbiscan"
        },
        "optimism": {
            "url": "https://api-optimistic.etherscan.io/api",
            "name": "Optimism Etherscan"
        },
        "avalanche": {
            "url": "https://api.snowtrace.io/api",
            "name": "SnowTrace"
        },
        "fantom": {
            "url": "https://api.ftmscan.com/api",
            "name": "FTMScan"
        }
    }
    
    def __init__(self, api_key: Optional[str] = None, chain: str = "ethereum"):
        # Use provided API key, or get from config, or use default
        if api_key:
            self.api_key = api_key
        else:
            chain_lower = chain.lower()
            config_key = config.get_api_key(chain_lower)
            self.api_key = config_key if config_key else "YourApiKeyToken"
        
        self.chain = chain.lower()
        
        if self.chain not in self.EXPLORERS:
            logger.warning(f"Unsupported chain: {chain}. Defaulting to ethereum")
            self.chain = "ethereum"
        
        self.base_url = self.EXPLORERS[self.chain]["url"]
        self.explorer_name = self.EXPLORERS[self.chain]["name"]
        logger.info(f"Initialized {self.explorer_name} API for {self.chain}")

    
    def get_contract_source(self, contract_address: str) -> Dict[str, Any]:
        """
        Fetches verified contract source code from block explorer.
        """
        params = {
            "module": "contract",
            "action": "getsourcecode",
            "address": contract_address,
            "apikey": self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data["status"] == "1" and data["result"]:
                result = data["result"][0]
                
                # Check if contract is verified
                if not result.get("SourceCode"):
                    logger.warning(f"Contract not verified on {self.explorer_name}: {contract_address}")
                    return {}
                
                return {
                    "source_code": result.get("SourceCode", ""),
                    "contract_name": result.get("ContractName", ""),
                    "compiler_version": result.get("CompilerVersion", ""),
                    "optimization": result.get("OptimizationUsed", ""),
                    "runs": result.get("Runs", ""),
                    "constructor_args": result.get("ConstructorArguments", ""),
                    "proxy": result.get("Proxy", "0"),
                    "chain": self.chain,
                    "explorer": self.explorer_name
                }
            else:
                logger.warning(f"Contract not verified or not found on {self.explorer_name}: {contract_address}")
                return {}
        except Exception as e:
            logger.error(f"{self.explorer_name} API error: {e}")
            return {}
    
    def get_contract_abi(self, contract_address: str) -> list:
        """
        Fetches contract ABI from block explorer.
        """
        params = {
            "module": "contract",
            "action": "getabi",
            "address": contract_address,
            "apikey": self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data["status"] == "1":
                import json
                return json.loads(data["result"])
            return []
        except Exception as e:
            logger.error(f"Error fetching ABI from {self.explorer_name}: {e}")
            return []
    
    def get_transaction_list(self, contract_address: str, page: int = 1, offset: int = 100) -> list:
        """
        Fetches recent transactions for a contract address.
        """
        params = {
            "module": "account",
            "action": "txlist",
            "address": contract_address,
            "page": page,
            "offset": offset,
            "sort": "desc",
            "apikey": self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data["status"] == "1":
                return data["result"]
            return []
        except Exception as e:
            logger.error(f"Error fetching transactions from {self.explorer_name}: {e}")
            return []
    
    def check_if_proxy(self, contract_address: str) -> bool:
        """
        Checks if a contract is a proxy.
        """
        source_data = self.get_contract_source(contract_address)
        return source_data.get("proxy", "0") == "1"
    
    @staticmethod
    def get_supported_chains():
        """
        Returns list of supported blockchain networks.
        """
        return list(EtherscanAPI.EXPLORERS.keys())
