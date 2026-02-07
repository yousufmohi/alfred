"""
GitHub OAuth authentication for Alfred
Handles device flow login and token management
"""

import json
import time
import webbrowser
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime, timedelta
import requests


class GitHubAuth:
    """Handle GitHub OAuth authentication using device flow"""
    
    CLIENT_ID = "Ov23liACzLcUYB6MHfmV"  
    
    def __init__(self, config_dir: Path):
        """Initialize GitHub auth manager"""
        self.config_dir = config_dir
        self.token_file = config_dir / "github_token.json"
    
    def is_logged_in(self) -> bool:
        """Check if user has valid token"""
        token_data = self._load_token()
        if not token_data:
            return False
        
        # Check expiry
        expires_at = token_data.get('expires_at')
        if expires_at:
            if datetime.now() >= datetime.fromisoformat(expires_at):
                return False
        
        return True
    
    def get_token(self) -> Optional[str]:
        """Get valid GitHub token"""
        if not self.is_logged_in():
            return None
        return self._load_token().get('access_token')
    
    def login(self) -> Dict:
        """
        Start GitHub login (device flow)
        
        Returns:
            Dict with user_code and verification_uri
        """
        response = requests.post(
            "https://github.com/login/device/code",
            headers={"Accept": "application/json"},
            data={
                "client_id": self.CLIENT_ID,
                "scope": "repo read:user"
            }
        )
        
        if response.status_code != 200:
            return {"success": False, "error": "Failed to start login"}
        
        return {**response.json(), "success": True}
    
    def poll_for_token(self, device_code: str, interval: int = 5) -> Dict:
        """
        Wait for user to authorize and get token
        
        Args:
            device_code: From login()
            interval: Seconds between checks
            
        Returns:
            Dict with success status
        """
        timeout = time.time() + 900  # 15 minute timeout
        
        while time.time() < timeout:
            time.sleep(interval)
            
            response = requests.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data={
                    "client_id": self.CLIENT_ID,
                    "device_code": device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
                }
            )
            
            data = response.json()
            
            if 'access_token' in data:
                # Success! Save token
                self._save_token({
                    'access_token': data['access_token'],
                    'token_type': data.get('token_type', 'bearer'),
                    'scope': data.get('scope', ''),
                    'expires_at': (datetime.now() + timedelta(days=365)).isoformat(),
                    'created_at': datetime.now().isoformat()
                })
                return {"success": True}
            
            error = data.get('error')
            if error == 'authorization_pending':
                continue  # Keep waiting
            elif error == 'slow_down':
                interval += 5  # Slow down polling
                continue
            elif error in ['expired_token', 'access_denied']:
                return {"success": False, "error": error}
        
        return {"success": False, "error": "timeout"}
    
    def logout(self):
        """Clear stored token"""
        if self.token_file.exists():
            self.token_file.unlink()
    
    def get_user_info(self) -> Optional[Dict]:
        """Get GitHub user info"""
        token = self.get_token()
        if not token:
            return None
        
        try:
            response = requests.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            return response.json() if response.status_code == 200 else None
        except:
            return None
    
    def get_token_info(self) -> Optional[Dict]:
        """Get token metadata"""
        token_data = self._load_token()
        if not token_data:
            return None
        
        expires_at = datetime.fromisoformat(token_data['expires_at'])
        hours_left = (expires_at - datetime.now()).total_seconds() / 3600
        
        return {
            'scope': token_data.get('scope'),
            'hours_until_expiry': round(hours_left, 1),
            'created_at': token_data['created_at']
        }
    
    def _save_token(self, token_data: Dict):
        """Save token securely"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.token_file, 'w') as f:
            json.dump(token_data, f, indent=2)
        self.token_file.chmod(0o600)  # Only user can read
    
    def _load_token(self) -> Optional[Dict]:
        """Load token from file"""
        if not self.token_file.exists():
            return None
        try:
            with open(self.token_file, 'r') as f:
                return json.load(f)
        except:
            return None