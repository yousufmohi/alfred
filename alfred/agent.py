"""
Core code review agent
"""

import anthropic
import os
from pathlib import Path
from typing import Optional
from .prompts import SYSTEM_PROMPT, get_review_prompt
from .config import Config


class CodeReviewAgent:
    """AI agent that reviews code using Claude"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the agent with Anthropic API"""
        # Use config system to get API key
        config = Config()
        self.api_key = config.get_api_key(api_key)
        
        if not self.api_key:
            raise ValueError(
                "API key not found. Run 'alfred setup' to configure."
            )
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-20250514"
    
    def read_file(self, filepath: str) -> str:
        """Read code file from disk"""
        path = Path(filepath)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        if not path.is_file():
            raise ValueError(f"Path is not a file: {filepath}")
        
        # Read with error handling for encoding issues
        try:
            return path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            # Try with latin-1 as fallback
            return path.read_text(encoding='latin-1')
    
    def review_code(
        self, 
        filepath: str, 
        focus: str = "general",
        max_tokens: int = 4000
    ) -> str:
        """
        Review a code file
        
        Args:
            filepath: Path to the code file
            focus: Review focus area (general, security, performance, style, bugs)
            max_tokens: Maximum tokens for response
            
        Returns:
            Review as formatted text
        """
        # Read the code
        code = self.read_file(filepath)
        filename = Path(filepath).name
        
        # Generate review prompt
        user_prompt = get_review_prompt(code, filename, focus)
        
        # Call Claude
        message = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )
        
        # Extract response
        return message.content[0].text
    
    def review_multiple(self, filepaths: list[str], focus: str = "general") -> dict[str, str]:
        """Review multiple files"""
        results = {}
        
        for filepath in filepaths:
            try:
                results[filepath] = self.review_code(filepath, focus)
            except Exception as e:
                results[filepath] = f"Error reviewing file: {str(e)}"
        
        return results