"""
Configuration management for Alfred
Handles API key storage and retrieval
"""

import json
import os
from pathlib import Path
from typing import Optional


class Config:
    """Manage Alfred configuration"""
    
    def __init__(self):
        """Initialize config with default paths"""
        self.config_dir = Path.home() / ".alfred"
        self.config_file = self.config_dir / "config.json"
        self._ensure_config_dir()
    
    def _ensure_config_dir(self):
        """Create config directory if it doesn't exist"""
        self.config_dir.mkdir(exist_ok=True)
        # Set permissions to 700 (only user can read/write/execute)
        self.config_dir.chmod(0o700)
    
    def get_api_key(self, cli_key: Optional[str] = None) -> Optional[str]:
        """
        Get API key from multiple sources in priority order:
        1. CLI argument (--api-key)
        2. Config file (~/.alfred/config.json)
        3. Environment variable (ANTHROPIC_API_KEY)
        
        Args:
            cli_key: API key passed via command line
            
        Returns:
            API key or None if not found
        """
        # Priority 1: CLI argument
        if cli_key:
            return cli_key
        
        # Priority 2: Config file
        config_key = self.load_config().get("api_key")
        if config_key:
            return config_key
        
        # Priority 3: Environment variable
        env_key = os.getenv("ANTHROPIC_API_KEY")
        if env_key:
            return env_key
        
        return None
    
    def load_config(self) -> dict:
        """Load configuration from file"""
        if not self.config_file.exists():
            return {}
        
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    
    def save_config(self, config: dict):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Set permissions to 600 (only user can read/write)
        self.config_file.chmod(0o600)
    
    def save_api_key(self, api_key: str):
        """Save API key to config file"""
        config = self.load_config()
        config["api_key"] = api_key
        self.save_config(config)
    
    def get_masked_key(self) -> Optional[str]:
        """Get masked version of API key for display"""
        key = self.get_api_key()
        if not key:
            return None
        
        # Show first 7 and last 4 characters
        if len(key) > 15:
            return f"{key[:7]}...{key[-4:]}"
        return "***"
    
    def clear_config(self):
        """Clear all configuration"""
        if self.config_file.exists():
            self.config_file.unlink()
    
    def has_api_key(self) -> bool:
        """Check if API key is configured anywhere"""
        return self.get_api_key() is not None
    
    def get_config_location(self) -> str:
        """Get the config file location"""
        return str(self.config_file)