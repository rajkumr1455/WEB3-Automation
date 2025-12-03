"""
API Key and Address Validation Utilities
Validates format and structure of API keys and blockchain addresses

Usage:
    from src.utils.key_validator import validate_claude_key, validate_ethereum_address
    
    if not validate_claude_key(os.getenv('CLAUDE_API_KEY')):
        logger.error("Invalid Claude API key format")
"""

import re
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def validate_claude_key(key: Optional[str]) -> bool:
    """
    Validate Anthropic Claude API key format
    
    Claude keys format: sk-ant-api03-[95 characters base64-like]
    
    Args:
        key: API key to validate
        
    Returns:
        True if key format is valid
    """
    if not key:
        return False
    
    # Claude keys: sk-ant-api03-[base64 chars]
    # Length: sk-ant-api03- (12) + 95 chars = 107 total
    pattern = r'^sk-ant-api\d{2}-[A-Za-z0-9_-]{95}$'
    
    if not re.match(pattern, key):
        logger.debug(f"Claude key validation failed: invalid format (length: {len(key)})")
        return False
    
    return True


def validate_openai_key(key: Optional[str]) -> bool:
    """
    Validate OpenAI API key format
    
    OpenAI keys format: sk-[48+ alphanumeric characters]
    
    Args:
        key: API key to validate
        
    Returns:
        True if key format is valid
    """
    if not key:
        return False
    
    # OpenAI keys: sk-[alphanumeric] (48+ chars total)
    pattern = r'^sk-[A-Za-z0-9]{48,}$'
    
    if not re.match(pattern, key):
        logger.debug(f"OpenAI key validation failed: invalid format")
        return False
    
    return True


def validate_etherscan_key(key: Optional[str]) -> bool:
    """
    Validate Etherscan API key format
    
    Etherscan keys: 34 uppercase alphanumeric characters
    
    Args:
        key: API key to validate
        
    Returns:
        True if key format is valid
    """
    if not key:
        return False
    
    # Etherscan keys: 34 alphanumeric chars (usually uppercase)
    pattern = r'^[A-Z0-9]{34}$'
    
    if not re.match(pattern, key):
        logger.debug(f"Etherscan key validation failed: invalid format (length: {len(key)})")
        return False
    
    return True


def validate_ethereum_address(address: Optional[str], check_checksum: bool = False) -> bool:
    """
    Validate Ethereum address format
    
    Args:
        address: Ethereum address (0x + 40 hex chars)
        check_checksum: If True, validate EIP-55 checksum (requires web3)
        
    Returns:
        True if address format is valid
    """
    if not address:
        return False
    
    # Basic format: 0x + 40 hex characters
    pattern = r'^0x[a-fA-F0-9]{40}$'
    
    if not re.match(pattern, address):
        logger.debug(f"Ethereum address validation failed: invalid format")
        return False
    
    if check_checksum:
        try:
            from web3 import Web3
            # Web3.is_checksum_address validates EIP-55
            if not Web3.is_checksum_address(address):
                logger.warning(f"Address {address[:10]}... failed checksum validation")
                return False
        except ImportError:
            logger.debug("web3 not installed - skipping checksum validation")
    
    return True


def validate_contract_address(address: Optional[str]) -> bool:
    """
    Validate contract address format (alias for validate_ethereum_address)
    
    Args:
        address: Contract address
        
    Returns:
        True if address format is valid
    """
    return validate_ethereum_address(address)


def validate_rpc_url(url: Optional[str]) -> bool:
    """
    Validate RPC URL format
    
    Args:
        url: RPC endpoint URL
        
    Returns:
        True if URL format is valid
    """
    if not url:
        return False
    
    # Must be http/https URL
    pattern = r'^https?://[a-zA-Z0-9\-\.]+(:[0-9]+)?(/.*)?$'
    
    if not re.match(pattern, url):
        logger.debug(f"RPC URL validation failed: invalid format")
        return False
    
    # Warn if using http (insecure)
    if url.startswith('http://') and 'localhost' not in url and '127.0.0.1' not in url:
        logger.warning(f"RPC URL uses insecure HTTP: {url[:50]}...")
    
    return True


def mask_secret(secret: Optional[str], reveal_chars: int = 4) -> str:
    """
    Mask secret for safe logging
    
    Args:
        secret: Secret to mask
        reveal_chars: Number of characters to reveal at end
        
    Returns:
        Masked string (e.g., "sk-ant-****abcd")
    """
    if not secret:
        return "<empty>"
    
    if len(secret) <= reveal_chars:
        return "*" * len(secret)
    
    # Find last dash or use middle point
    last_dash = secret.rfind('-')
    if last_dash > 0:
        prefix = secret[:last_dash + 1]
        suffix = secret[-reveal_chars:]
        return f"{prefix}****{suffix}"
    
    return f"{secret[:4]}****{secret[-reveal_chars:]}"


def validate_all_keys(env_vars: dict) -> dict:
    """
    Validate all API keys and addresses in environment
    
    Args:
        env_vars: Dictionary of environment variables
        
    Returns:
        Dictionary with validation results
    """
    results = {}
    
    # Claude API key
    claude_key = env_vars.get('CLAUDE_API_KEY')
    results['CLAUDE_API_KEY'] = {
        'valid': validate_claude_key(claude_key),
        'present': bool(claude_key),
        'masked': mask_secret(claude_key) if claude_key else None
    }
    
    # OpenAI API key
    openai_key = env_vars.get('OPENAI_API_KEY')
    results['OPENAI_API_KEY'] = {
        'valid': validate_openai_key(openai_key),
        'present': bool(openai_key),
        'masked': mask_secret(openai_key) if openai_key else None
    }
    
    # Etherscan API keys
    for chain in ['ETHERSCAN', 'BSCSCAN', 'POLYGONSCAN', 'ARBISCAN', 'OPTIMISM', 'BASESCAN']:
        key_name = f'{chain}_API_KEY'
        key = env_vars.get(key_name)
        results[key_name] = {
            'valid': validate_etherscan_key(key) if key else False,
            'present': bool(key),
            'masked': mask_secret(key, 6) if key else None
        }
    
    # RPC URLs
    for rpc_key in ['ETHEREUM_RPC_URL', 'ETHEREUM_RPC_URL_BACKUP', 'BSC_RPC_URL', 'POLYGON_RPC_URL']:
        url = env_vars.get(rpc_key)
        results[rpc_key] = {
            'valid': validate_rpc_url(url) if url else False,
            'present': bool(url),
            'masked': url[:50] + '...' if url and len(url) > 50 else url
        }
    
    return results


# CLI utility for testing
if __name__ == "__main__":
    import os
    import json
    
    print("=== API Key Validator ===\n")
    
    # Test with environment variables
    results = validate_all_keys(os.environ)
    
    print(json.dumps(results, indent=2))
    
    # Summary
    valid_count = sum(1 for r in results.values() if r['valid'])
    present_count = sum(1 for r in results.values() if r['present'])
    
    print(f"\nSummary:")
    print(f"  Keys present: {present_count}/{len(results)}")
    print(f"  Keys valid: {valid_count}/{present_count if present_count > 0 else 1}")
    
    if valid_count < present_count:
        print("\n⚠️  Some keys have invalid format - check configuration")
    else:
        print("\n✅ All present keys are valid")
