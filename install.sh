#!/bin/bash
# Alfred Easy Installer for Mac/Linux
# Run with: bash install.sh
# Or: chmod +x install.sh && ./install.sh

set -e  # Exit on error

echo "========================================"
echo "Alfred Easy Installer"
echo "========================================"
echo ""
echo "Note: If you get a 'permission denied' error,"
echo "run: chmod +x install.sh && ./install.sh"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed"
    echo ""
    echo "Install Python:"
    echo "  Mac: brew install python3"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "  Fedora: sudo dnf install python3 python3-pip"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "[OK] Python found: $PYTHON_VERSION"

echo ""
echo "[1/5] Installing Poetry and dependencies..."
python3 -m pip install --quiet --user poetry
poetry install --quiet
echo "Done."

echo ""
echo "[2/5] Installing pipx..."
python3 -m pip install --quiet --user pipx
echo "Done."

echo ""
echo "[3/5] Setting up pipx paths..."
python3 -m pipx ensurepath
echo "Done."

echo ""
echo "[4/5] Installing Alfred..."
# Uninstall if exists
python3 -m pipx uninstall alfred 2>/dev/null || true

# Install
python3 -m pipx install .
echo "Done."

echo ""
echo "[5/5] Testing installation..."
echo ""

# Test
if ~/.local/bin/alfred version 2>/dev/null; then
    echo ""
    echo "========================================"
    echo "SUCCESS! Alfred is installed"
    echo "========================================"
else
    echo ""
    echo "[WARNING] Installation completed but test failed"
    echo "This might be normal - try closing and reopening your terminal"
fi

echo ""
echo "Setting up permanent PATH..."

# Detect shell and profile file
if [ -n "$ZSH_VERSION" ]; then
    PROFILE_FILE="$HOME/.zshrc"
elif [ -n "$BASH_VERSION" ]; then
    PROFILE_FILE="$HOME/.bashrc"
else
    PROFILE_FILE="$HOME/.profile"
fi

# Check if PATH is already in profile
PATH_LINE='export PATH="$HOME/.local/bin:$PATH"'
if ! grep -q ".local/bin" "$PROFILE_FILE" 2>/dev/null; then
    echo "" >> "$PROFILE_FILE"
    echo "# Added by Alfred installer" >> "$PROFILE_FILE"
    echo "$PATH_LINE" >> "$PROFILE_FILE"
    echo "[OK] Added to $PROFILE_FILE"
    
    # Reload profile immediately
    source "$PROFILE_FILE" 2>/dev/null || . "$PROFILE_FILE" 2>/dev/null
    echo "[OK] Profile reloaded - alfred command is now available!"
    echo ""
    echo "Try it now: alfred --help"
else
    echo "[OK] Already in $PROFILE_FILE"
    
    # Reload anyway
    source "$PROFILE_FILE" 2>/dev/null || . "$PROFILE_FILE" 2>/dev/null
    echo "[OK] Profile reloaded - alfred command should work now!"
fi

echo ""
echo "========================================"
echo "Installation Complete!"
echo "========================================"
echo ""
echo "Testing alfred command..."

# Try to run alfred
if command -v alfred &> /dev/null; then
    echo "[SUCCESS] 'alfred' command works!"
    echo ""
    echo "Next steps:"
    echo "  alfred setup"
    echo "  alfred review yourfile.py"
else
    echo "[INFO] 'alfred' command not available yet"
    echo ""
    echo "This is normal. Alfred will work after you:"
    echo "  1. Close this terminal"
    echo "  2. Open a NEW terminal"
    echo "  3. Type: alfred --help"
    echo ""
    echo "Or use the full path right now:"
    echo "  $HOME/.local/bin/alfred --help"
fi

echo ""