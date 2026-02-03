#!/usr/bin/env python
"""
Entry point for Alfred CLI
This file is used by PyInstaller to build the standalone executable
"""

import sys
from alfred.cli import app

if __name__ == "__main__":
    app()