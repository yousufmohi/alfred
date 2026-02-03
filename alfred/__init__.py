"""
Alfred - AI-powered code reviewer
"""

__version__ = "0.1.0"

from .agent import CodeReviewAgent
from .cli import app
from .config import Config

__all__ = ["CodeReviewAgent", "app", "Config"]