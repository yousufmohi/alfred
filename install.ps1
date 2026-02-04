# Alfred Easy Installer for Windows (PowerShell)
# Run with: .\install.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Alfred Easy Installer" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Python from https://python.org" -ForegroundColor Yellow
    Write-Host 'Make sure to check "Add Python to PATH" during installation' -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "[1/5] Installing Poetry and dependencies..." -ForegroundColor Yellow
try {
    # Install Poetry
    pip install --quiet poetry
    
    # Install project dependencies
    poetry install --quiet
    Write-Host "Done." -ForegroundColor Green
} catch {
    Write-Host "WARNING: Poetry dependencies had issues, continuing anyway..." -ForegroundColor Yellow
}
Write-Host ""

Write-Host "[2/5] Installing pipx..." -ForegroundColor Yellow
try {
    pip install --quiet pipx
    
    # Add Python Scripts to PATH immediately so pipx works in this session
    $pythonScripts = python -c "import sysconfig; print(sysconfig.get_path('scripts'))"
    if ($pythonScripts) {
        $env:PATH += ";$pythonScripts"
        Write-Host "Added Python Scripts to PATH for this session" -ForegroundColor Green
    }
    
    Write-Host "Done." -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to install pipx" -ForegroundColor Red
    Write-Host $_.Exception.Message
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "[3/5] Setting up pipx paths..." -ForegroundColor Yellow
try {
    python -m pipx ensurepath 2>&1 | Out-Null
} catch {
    Write-Host "[WARNING] pipx ensurepath failed, but continuing..." -ForegroundColor Yellow
}

# Manually ensure PATH is set (backup)
$pipxBin = "$env:USERPROFILE\.local\bin"
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$pipxBin*") {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$pipxBin", "User")
    Write-Host "Added $pipxBin to system PATH" -ForegroundColor Green
}

# Also add to current session
$env:PATH += ";$pipxBin"
Write-Host "Done." -ForegroundColor Green

Write-Host ""
Write-Host "[4/5] Installing Alfred..." -ForegroundColor Yellow
# Uninstall if exists (using python -m pipx instead of pipx command)
python -m pipx uninstall alfred 2>&1 | Out-Null

# Install
try {
    python -m pipx install .
    Write-Host "Done." -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to install Alfred" -ForegroundColor Red
    Write-Host $_.Exception.Message
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "[5/5] Testing installation..." -ForegroundColor Yellow
Write-Host ""

# Add pipx bin to PATH for this session
$env:PATH += ";$env:USERPROFILE\.local\bin"

# Test
try {
    & "$env:USERPROFILE\.local\bin\alfred.exe" version
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "SUCCESS! Alfred is installed" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "[WARNING] Installation completed but test failed" -ForegroundColor Yellow
    Write-Host "This might be normal - try closing and reopening your terminal" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "IMPORTANT: Setting up permanent PATH..." -ForegroundColor Cyan

# Check if profile exists, create if not
if (!(Test-Path $PROFILE)) {
    New-Item -Path $PROFILE -Type File -Force | Out-Null
    Write-Host "[OK] Created PowerShell profile" -ForegroundColor Green
}

# Check if PATH is already in profile
$pathLine = '$env:PATH += ";$env:USERPROFILE\.local\bin"'
$profileContent = Get-Content $PROFILE -ErrorAction SilentlyContinue

if ($profileContent -notcontains $pathLine) {
    Add-Content $PROFILE "`n# Added by Alfred installer`n$pathLine"
    Write-Host "[OK] Added to PowerShell profile" -ForegroundColor Green
    
    # Reload profile immediately
    . $PROFILE
    Write-Host "[OK] Profile reloaded - alfred command is now available!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Try it now: alfred --help" -ForegroundColor Cyan
} else {
    Write-Host "[OK] Already in PowerShell profile" -ForegroundColor Green
    
    # Reload anyway
    . $PROFILE
    Write-Host "[OK] Profile reloaded - alfred command should work now!" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Installation Complete!" -ForegroundColor Green  
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Testing alfred command..." -ForegroundColor Cyan

# Try to run alfred
try {
    alfred --version 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[SUCCESS] 'alfred' command works!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Cyan
        Write-Host "  alfred setup" -ForegroundColor White
        Write-Host "  alfred review yourfile.py" -ForegroundColor White
    } else {
        throw "Command failed"
    }
} catch {
    Write-Host "[INFO] 'alfred' command not available yet" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "This is normal. Alfred will work after you:" -ForegroundColor Cyan
    Write-Host "  1. Close this PowerShell window" -ForegroundColor White
    Write-Host "  2. Open a NEW PowerShell window" -ForegroundColor White
    Write-Host "  3. Type: alfred --help" -ForegroundColor White
    Write-Host ""
    Write-Host "Or use the full path right now:" -ForegroundColor Cyan  
    Write-Host "  $env:USERPROFILE\.local\bin\alfred.exe --help" -ForegroundColor Yellow
}

Write-Host ""
Write-Host ""

Read-Host "Press Enter to exit"