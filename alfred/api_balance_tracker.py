"""
Real-time API balance tracking for Alfred
Fetches actual remaining credits from Anthropic
"""

import anthropic
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from .config import Config
from .cost_tracker import CostTracker


class APIBalanceTracker:
    """Track real API balance from Anthropic"""
    
    def __init__(self, config_dir: Path, api_key: Optional[str] = None):
        """
        Initialize balance tracker
        
        Args:
            config_dir: Config directory
            api_key: Anthropic API key
        """
        self.config_dir = config_dir
        config = Config()
        self.api_key = config.get_api_key(api_key)
        self.cost_tracker = CostTracker(config_dir)
        
        if self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
        else:
            self.client = None
    
    def get_account_balance(self) -> Optional[Dict]:
        """
        Get actual account balance from Anthropic API
        
        Note: Anthropic doesn't have a public balance API endpoint yet,
        so we track usage locally and show estimated remaining based on
        user's reported balance.
        
        Returns:
            Dict with balance info or None if unavailable
        """
        # Anthropic doesn't expose balance via API yet
        # We need to use local tracking + user input
        return None
    
    def get_usage_status(self, user_balance: Optional[float] = None) -> Dict:
        """
        Get usage status based on actual balance
        
        Args:
            user_balance: User's current balance from Anthropic console
            
        Returns:
            Dict with usage info
        """
        # Get this month's spending
        month_cost = self._get_current_month_cost()
        
        # Get total all-time spending
        total_usage = self.cost_tracker.get_total_usage()
        total_cost = total_usage['total_cost']
        
        if user_balance is None:
            # No balance set - just show usage
            return {
                'has_balance': False,
                'month_cost': month_cost,
                'total_cost': total_cost,
                'message': f"💰 Used ${month_cost:.2f} this month (${total_cost:.2f} total)"
            }
        
        # Calculate remaining
        remaining = user_balance
        
        # Estimate if we have enough for more reviews
        avg_cost_per_review = total_usage.get('avg_cost_per_review', 0.15)
        estimated_reviews_left = int(remaining / avg_cost_per_review) if avg_cost_per_review > 0 else 0
        
        # Determine status
        if remaining < 1:
            status = 'low'
            message = f"⚠️  Low balance: ${remaining:.2f} remaining (~{estimated_reviews_left} reviews)"
        elif remaining < 5:
            status = 'warning'
            message = f"⚠️  Running low: ${remaining:.2f} remaining (~{estimated_reviews_left} reviews)"
        else:
            status = 'ok'
            message = f"✅ ${remaining:.2f} remaining (~{estimated_reviews_left} reviews)"
        
        return {
            'has_balance': True,
            'status': status,
            'balance': remaining,
            'month_cost': month_cost,
            'total_cost': total_cost,
            'estimated_reviews_left': estimated_reviews_left,
            'avg_cost_per_review': avg_cost_per_review,
            'message': message,
            'should_warn': status in ['low', 'warning']
        }
    
    def _get_current_month_cost(self) -> float:
        """Get spending for current calendar month"""
        history = self.cost_tracker._load_history()
        current_month = datetime.now().strftime("%Y-%m")
        month_reviews = [
            r for r in history 
            if r['timestamp'].startswith(current_month)
        ]
        return sum(r['cost'] for r in month_reviews)
    
    def save_balance(self, balance: float):
        """
        Save user's current balance
        
        Args:
            balance: Current balance from Anthropic console
        """
        import json
        
        balance_file = self.config_dir / "api_balance.json"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        data = {
            'balance': balance,
            'last_updated': datetime.now().isoformat(),
            'total_cost_at_update': self.cost_tracker.get_total_usage()['total_cost']
        }
        
        with open(balance_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_balance(self) -> Optional[Dict]:
        """
        Load saved balance
        
        Returns:
            Dict with balance info or None
        """
        import json
        
        balance_file = self.config_dir / "api_balance.json"
        
        if not balance_file.exists():
            return None
        
        try:
            with open(balance_file, 'r') as f:
                data = json.load(f)
            
            # Calculate estimated current balance
            saved_balance = data['balance']
            saved_total_cost = data['total_cost_at_update']
            current_total_cost = self.cost_tracker.get_total_usage()['total_cost']
            
            # Estimated remaining = saved balance - (current cost - saved cost)
            spent_since_save = current_total_cost - saved_total_cost
            estimated_balance = saved_balance - spent_since_save
            
            return {
                'balance': max(0, estimated_balance),
                'last_updated': data['last_updated'],
                'spent_since_update': spent_since_save,
                'is_estimate': spent_since_save > 0
            }
        except:
            return None
    
    def get_detailed_status(self) -> Dict:
        """
        Get detailed status including saved balance
        
        Returns:
            Complete status dict
        """
        balance_data = self.load_balance()
        
        if balance_data:
            balance = balance_data['balance']
            status = self.get_usage_status(balance)
            status['last_updated'] = balance_data['last_updated']
            status['is_estimate'] = balance_data.get('is_estimate', False)
            status['spent_since_update'] = balance_data.get('spent_since_update', 0)
            return status
        else:
            return self.get_usage_status(None)
    
    def check_before_review(self, estimated_cost: float = 0.15) -> tuple[bool, Optional[str]]:
        """
        Check if review should proceed given balance
        
        Args:
            estimated_cost: Estimated cost of the review
            
        Returns:
            Tuple of (should_proceed, warning_message)
        """
        status = self.get_detailed_status()
        
        if not status['has_balance']:
            # No balance set - allow review
            return True, None
        
        balance = status['balance']
        
        # Check if we have enough balance
        if balance < estimated_cost:
            return False, (
                f"❌ Insufficient balance for this review!\n"
                f"   Current balance: ${balance:.2f}\n"
                f"   Estimated cost: ${estimated_cost:.2f}\n"
                f"   \n"
                f"   Add credits at: https://console.anthropic.com/\n"
                f"   Then update: alfred balance set <amount>"
            )
        
        if status['status'] in ['low', 'warning']:
            return True, (
                f"⚠️  {status['message']}\n"
                f"   This review will cost ~${estimated_cost:.2f}"
            )
        
        return True, None