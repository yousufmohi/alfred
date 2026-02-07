"""
Cost tracking for Alfred code reviews
Tracks token usage and estimates API costs
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List


class CostTracker:
    """Track API costs and token usage"""
    
    # Claude Sonnet 4 pricing (per million tokens)
    INPUT_COST_PER_M = 3.00   # $3 per 1M input tokens
    OUTPUT_COST_PER_M = 15.00  # $15 per 1M output tokens
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.history_file = config_dir / "cost_history.json"
        self.session_usage = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_cost": 0.0,
            "reviews": 0
        }
    
    def track_review(self, usage, filepath: str = None) -> Dict:
        """
        Track a single review's cost
        
        Args:
            usage: Response.usage object from Claude API
            filepath: Optional file that was reviewed
            
        Returns:
            Dict with cost breakdown
        """
        input_tokens = usage.input_tokens
        output_tokens = usage.output_tokens
        
        # Calculate costs
        input_cost = (input_tokens / 1_000_000) * self.INPUT_COST_PER_M
        output_cost = (output_tokens / 1_000_000) * self.OUTPUT_COST_PER_M
        total_cost = input_cost + output_cost
        
        # Update session totals
        self.session_usage["input_tokens"] += input_tokens
        self.session_usage["output_tokens"] += output_tokens
        self.session_usage["total_cost"] += total_cost
        self.session_usage["reviews"] += 1
        
        # Save to history
        review_data = {
            "timestamp": datetime.now().isoformat(),
            "filepath": filepath,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost": total_cost
        }
        self._save_to_history(review_data)
        
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost": total_cost,
            "input_cost": input_cost,
            "output_cost": output_cost
        }
    
    def get_session_summary(self) -> Dict:
        """Get summary of current session costs"""
        return {
            "reviews": self.session_usage["reviews"],
            "total_tokens": self.session_usage["input_tokens"] + self.session_usage["output_tokens"],
            "input_tokens": self.session_usage["input_tokens"],
            "output_tokens": self.session_usage["output_tokens"],
            "total_cost": self.session_usage["total_cost"],
            "avg_cost_per_review": (
                self.session_usage["total_cost"] / self.session_usage["reviews"]
                if self.session_usage["reviews"] > 0 else 0
            )
        }
    
    def get_total_usage(self) -> Dict:
        """Get all-time usage statistics"""
        if not self.history_file.exists():
            return {
                "total_reviews": 0,
                "total_tokens": 0,
                "total_cost": 0.0
            }
        
        history = self._load_history()
        
        total_reviews = len(history)
        total_tokens = sum(r["total_tokens"] for r in history)
        total_cost = sum(r["cost"] for r in history)
        
        return {
            "total_reviews": total_reviews,
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "avg_cost_per_review": total_cost / total_reviews if total_reviews > 0 else 0,
            "avg_tokens_per_review": total_tokens / total_reviews if total_reviews > 0 else 0
        }
    
    def get_recent_reviews(self, limit: int = 10) -> List[Dict]:
        """Get recent review history"""
        if not self.history_file.exists():
            return []
        
        history = self._load_history()
        return history[-limit:]  # Last N reviews
    
    def _save_to_history(self, review_data: Dict):
        """Append review to history file"""
        history = self._load_history()
        history.append(review_data)
        
        # Keep only last 1000 reviews to avoid file bloat
        if len(history) > 1000:
            history = history[-1000:]
        
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def _load_history(self) -> List[Dict]:
        """Load review history from file"""
        if not self.history_file.exists():
            return []
        
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []