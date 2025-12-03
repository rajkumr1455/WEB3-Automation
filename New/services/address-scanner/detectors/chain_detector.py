"""
Chain Detector Module

Auto-detects blockchain network from address format
"""

from enum import Enum
from typing import Optional
import re

class Chain(str, Enum):
    """Supported blockchain networks"""
    ETHEREUM = "ethereum"
    BSC = "bsc"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    SOLANA = "solana"
    APTOS = "aptos"
    SUI = "sui"
    STARKNET = "starknet"

class ChainDetector:
    """
    Auto-detect blockchain from address format
    
    Patterns:
    - EVM (Ethereum, BSC, Polygon, etc.): 0x + 40 hex characters
    - Solana: 32-44 base58 characters
    - Aptos/Sui: 0x + 64 hex characters  
    - Starknet: 0x + variable length (typically 50+)
    """
    
    # Base58 alphabet (Solana uses this)
    BASE58_ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    
    @classmethod
    def detect(cls, address: str) -> Chain:
        """
        Detect blockchain from address format
        
        Args:
            address: Contract/wallet address
            
        Returns:
            Detected blockchain enum
            
        Raises:
            ValueError: If address format is unknown
        """
        address = address.strip()
        
        # EVM chains (0x + 40 hex chars = 42 total)
        if cls._is_evm_address(address):
            return Chain.ETHEREUM  # Default to Ethereum for EVM addresses
        
        # Solana (32-44 base58 chars, no 0x prefix)
        if cls._is_solana_address(address):
            return Chain.SOLANA
        
        # Aptos/Sui (0x + 64 hex chars = 66 total)
        if cls._is_aptos_sui_address(address):
            return Chain.APTOS  # Default to Aptos
        
        # Starknet (0x + longer hex, typically > 50)
        if cls._is_starknet_address(address):
            return Chain.STARKNET
        
        raise ValueError(
            f"Unknown address format: {address}. "
            "Supported formats: "
            "EVM (0x + 40 hex), "
            "Solana (32-44 base58), "
            "Aptos/Sui (0x + 64 hex), "
            "Starknet"
        )
    
    @classmethod
    def _is_evm_address(cls, address: str) -> bool:
        """Check if address is EVM format (0x + 40 hex)"""
        if not address.startswith('0x') or len(address) != 42:
            return False
        try:
            int(address[2:], 16)  # Verify hex
            return True
        except ValueError:
            return False
    
    @classmethod
    def _is_solana_address(cls, address: str) -> bool:
        """Check if address is Solana format (32-44 base58)"""
        if address.startswith('0x'):
            return False
        if not (32 <= len(address) <= 44):
            return False
        # Check if all characters are in base58 alphabet
        return all(c in cls.BASE58_ALPHABET for c in address)
    
    @classmethod
    def _is_aptos_sui_address(cls, address: str) -> bool:
        """Check if address is Aptos/Sui format (0x + 64 hex)"""
        if not address.startswith('0x') or len(address) != 66:
            return False
        try:
            int(address[2:], 16)  # Verify hex
            return True
        except ValueError:
            return False
    
    @classmethod
    def _is_starknet_address(cls, address: str) -> bool:
        """Check if address is Starknet format"""
        if not address.startswith('0x'):
            return False
        if len(address) <= 50:  # Starknet addresses are typically longer
            return False
        try:
            int(address[2:], 16)  # Verify hex
            return True
        except ValueError:
            return False
    
    @classmethod
    def get_chain_info(cls, chain: Chain) -> dict:
        """
        Get information about a blockchain
        
        Args:
            chain: Blockchain enum
            
        Returns:
            Dict with chain information
        """
        chain_info = {
            Chain.ETHEREUM: {
                "name": "Ethereum",
                "type": "EVM",
                "explorer": "https://etherscan.io",
                "rpc": "https://eth.llamarpc.com"
            },
            Chain.BSC: {
                "name": "BNB Smart Chain",
                "type": "EVM",
                "explorer": "https://bscscan.com",
                "rpc": "https://bsc-dataseed.binance.org"
            },
            Chain.POLYGON: {
                "name": "Polygon",
                "type": "EVM",
                "explorer": "https://polygonscan.com",
                "rpc": "https://polygon-rpc.com"
            },
            Chain.ARBITRUM: {
                "name": "Arbitrum",
                "type": "EVM",
                "explorer": "https://arbiscan.io",
                "rpc": "https://arb1.arbitrum.io/rpc"
            },
            Chain.OPTIMISM: {
                "name": "Optimism",
                "type": "EVM",
                "explorer": "https://optimistic.etherscan.io",
                "rpc": "https://mainnet.optimism.io"
            },
            Chain.SOLANA: {
                "name": "Solana",
                "type": "Solana",
                "explorer": "https://explorer.solana.com",
                "rpc": "https://api.mainnet-beta.solana.com"
            },
            Chain.APTOS: {
                "name": "Aptos",
                "type": "Move",
                "explorer": "https://explorer.aptoslabs.com",
                "rpc": "https://fullnode.mainnet.aptoslabs.com/v1"
            },
            Chain.SUI: {
                "name": "Sui",
                "type": "Move",
                "explorer": "https://explorer.sui.io",
                "rpc": "https://fullnode.mainnet.sui.io"
            },
            Chain.STARKNET: {
                "name": "Starknet",
                "type": "Cairo",
                "explorer": "https://starkscan.co",
                "rpc": "https://starknet-mainnet.public.blastapi.io"
            }
        }
        
        return chain_info.get(chain, {"name": "Unknown", "type": "Unknown"})
