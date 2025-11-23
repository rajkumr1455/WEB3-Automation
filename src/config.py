"""
Configuration Manager for Web3 Hunter
Centralized configuration and API key management
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

class Config:
    """Centralized configuration manager"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize configuration from .env and config files"""
        # Load .env file
        env_path = Path(__file__).parent.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)
        
        # Load yaml config if exists
        config_path = Path(__file__).parent.parent / 'config' / 'settings.yaml'
        if config_path.exists():
            with open(config_path, 'r') as f:
                yaml_config = yaml.safe_load(f) or {}
        else:
            yaml_config = {}
        
        # Merge environment variables with yaml config
        self._config = {
            # API Keys
            'openai_api_key': os.getenv('OPENAI_API_KEY', yaml_config.get('openai_api_key', '')),
            
            # Block Explorer API Keys
            'api_keys': {
                'ethereum': os.getenv('ETHERSCAN_API_KEY', yaml_config.get('api_keys', {}).get('ethereum', '')),
                'base': os.getenv('BASESCAN_API_KEY', yaml_config.get('api_keys', {}).get('base', '')),
                'polygon': os.getenv('POLYGONSCAN_API_KEY', yaml_config.get('api_keys', {}).get('polygon', '')),
                'bsc': os.getenv('BSCSCAN_API_KEY', yaml_config.get('api_keys', {}).get('bsc', '')),
                'arbitrum': os.getenv('ARBISCAN_API_KEY', yaml_config.get('api_keys', {}).get('arbitrum', '')),
                'optimism': os.getenv('OPTIMISM_API_KEY', yaml_config.get('api_keys', {}).get('optimism', '')),
                'avalanche': os.getenv('SNOWTRACE_API_KEY', yaml_config.get('api_keys', {}).get('avalanche', '')),
                'fantom': os.getenv('FTMSCAN_API_KEY', yaml_config.get('api_keys', {}).get('fantom', '')),
            },
            
            # LLM Settings
            'llm': {
                'model': os.getenv('LLM_MODEL', yaml_config.get('llm', {}).get('model', 'gpt-4')),
                'temperature': float(os.getenv('LLM_TEMPERATURE', yaml_config.get('llm', {}).get('temperature', 0.1))),
                'max_tokens': int(os.getenv('LLM_MAX_TOKENS', yaml_config.get('llm', {}).get('max_tokens', 4000))),
            },
            
            # Analysis Settings
            'analysis': {
                'max_time': int(os.getenv('MAX_ANALYSIS_TIME', yaml_config.get('analysis', {}).get('max_time', 300))),
                'detailed_logging': os.getenv('ENABLE_DETAILED_LOGGING', str(yaml_config.get('analysis', {}).get('detailed_logging', True))).lower() == 'true',
            },
            
            # Report Settings
            'report': {
                'format': os.getenv('REPORT_FORMAT', yaml_config.get('report', {}).get('format', 'html')),
                'include_poc': os.getenv('INCLUDE_POC', str(yaml_config.get('report', {}).get('include_poc', True))).lower() == 'true',
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value
    
    def get_api_key(self, chain: str) -> Optional[str]:
        """Get API key for specific blockchain"""
        return self._config['api_keys'].get(chain, '')
    
    def get_openai_key(self) -> str:
        """Get OpenAI API key"""
        return self._config['openai_api_key']
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration"""
        return self._config['llm']
    
    def get_analysis_config(self) -> Dict[str, Any]:
        """Get analysis configuration"""
        return self._config['analysis']
    
    def get_report_config(self) -> Dict[str, Any]:
        """Get report configuration"""
        return self._config['report']
    
    @property
    def all(self) -> Dict[str, Any]:
        """Get all configuration"""
        return self._config.copy()


# Singleton instance
config = Config()
