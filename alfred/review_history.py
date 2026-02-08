"""
Review history tracking for Alfred
Stores and retrieves past code reviews
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class ReviewHistory:
    """Track and retrieve review history"""
    
    def __init__(self, config_dir: Path):
        """
        Initialize review history
        
        Args:
            config_dir: Config directory (e.g., ~/.alfred)
        """
        self.config_dir = config_dir
        self.history_file = config_dir / "review_history.json"
        self.max_reviews = 100  # Keep last 100 reviews
    
    def save_review(
        self,
        filepath: str,
        review_text: str,
        focus: str = "general",
        score: Optional[int] = None,
        cost: Optional[float] = None
    ) -> int:
        """
        Save a review to history
        
        Args:
            filepath: Path to reviewed file
            review_text: Full review text
            focus: Review focus area
            score: Overall score (1-10)
            cost: Review cost in dollars
            
        Returns:
            Review ID
        """
        history = self._load_history()
        
        # Generate review ID
        review_id = len(history) + 1
        
        # Extract score from review if not provided
        if score is None:
            score = self._extract_score(review_text)
        
        review_data = {
            "id": review_id,
            "filepath": str(filepath),
            "filename": Path(filepath).name,
            "review": review_text,
            "focus": focus,
            "score": score,
            "cost": cost,
            "timestamp": datetime.now().isoformat(),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        history.append(review_data)
        
        # Keep only last N reviews
        if len(history) > self.max_reviews:
            history = history[-self.max_reviews:]
        
        self._save_history(history)
        return review_id
    
    def get_review(self, review_id: int) -> Optional[Dict]:
        """
        Get a specific review by ID
        
        Args:
            review_id: Review ID
            
        Returns:
            Review dict or None
        """
        history = self._load_history()
        
        for review in history:
            if review['id'] == review_id:
                return review
        
        return None
    
    def get_recent(self, limit: int = 10) -> List[Dict]:
        """
        Get recent reviews
        
        Args:
            limit: Number of reviews to return
            
        Returns:
            List of review dicts
        """
        history = self._load_history()
        return history[-limit:][::-1]  # Last N, reversed (newest first)
    
    def get_all(self) -> List[Dict]:
        """
        Get all reviews
        
        Returns:
            List of all review dicts
        """
        return self._load_history()[::-1]  # Newest first
    
    def get_by_file(self, filepath: str) -> List[Dict]:
        """
        Get all reviews for a specific file
        
        Args:
            filepath: Path to file
            
        Returns:
            List of reviews for that file
        """
        history = self._load_history()
        filename = Path(filepath).name
        
        file_reviews = [
            r for r in history 
            if r['filename'] == filename or r['filepath'] == str(filepath)
        ]
        
        return file_reviews[::-1]  # Newest first
    
    def search(self, query: str) -> List[Dict]:
        """
        Search reviews by content
        
        Args:
            query: Search query
            
        Returns:
            List of matching reviews
        """
        history = self._load_history()
        query_lower = query.lower()
        
        matches = []
        for review in history:
            # Search in review text, filename, and focus
            if (query_lower in review['review'].lower() or
                query_lower in review['filename'].lower() or
                query_lower in review['focus'].lower()):
                matches.append(review)
        
        return matches[::-1]  # Newest first
    
    def get_stats(self) -> Dict:
        """
        Get review statistics
        
        Returns:
            Dict with stats
        """
        history = self._load_history()
        
        if not history:
            return {
                "total_reviews": 0,
                "avg_score": 0,
                "total_cost": 0,
                "files_reviewed": 0
            }
        
        scores = [r['score'] for r in history if r['score']]
        costs = [r['cost'] for r in history if r['cost']]
        files = set(r['filename'] for r in history)
        
        return {
            "total_reviews": len(history),
            "avg_score": sum(scores) / len(scores) if scores else 0,
            "total_cost": sum(costs) if costs else 0,
            "files_reviewed": len(files),
            "focus_breakdown": self._get_focus_breakdown(history)
        }
    
    def delete_review(self, review_id: int) -> bool:
        """
        Delete a review
        
        Args:
            review_id: Review ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        history = self._load_history()
        
        for i, review in enumerate(history):
            if review['id'] == review_id:
                history.pop(i)
                self._save_history(history)
                return True
        
        return False
    
    def clear_all(self) -> int:
        """
        Clear all review history
        
        Returns:
            Number of reviews deleted
        """
        history = self._load_history()
        count = len(history)
        self._save_history([])
        return count
    
    def _extract_score(self, review_text: str) -> Optional[int]:
        """Extract score from review text (e.g., 'Overall Score: 8/10')"""
        import re
        
        # Look for patterns like "Score: 8/10" or "8/10"
        patterns = [
            r'Overall Score:\s*(\d+)/10',
            r'Score:\s*(\d+)/10',
            r'Rating:\s*(\d+)/10',
            r'(\d+)/10'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, review_text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return None
    
    def _get_focus_breakdown(self, history: List[Dict]) -> Dict[str, int]:
        """Get count of reviews by focus area"""
        breakdown = {}
        for review in history:
            focus = review['focus']
            breakdown[focus] = breakdown.get(focus, 0) + 1
        return breakdown
    
    def _load_history(self) -> List[Dict]:
        """Load review history from file"""
        if not self.history_file.exists():
            return []
        
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    
    def _save_history(self, history: List[Dict]):
        """Save review history to file"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)