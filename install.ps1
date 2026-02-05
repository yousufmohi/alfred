# Alfred Easy Installer for Windows (PowerShell)
# Run with: .\install.ps1

Clear-Host


# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Python from https://python.org" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

function Show-Loading {
    param([string]$Message)
    
    Write-Host "  $Message" -NoNewline -ForegroundColor Cyan
    for ($i = 0; $i -lt 3; $i++) {
        Start-Sleep -Milliseconds 200
        Write-Host "." -NoNewline -ForegroundColor Cyan
    }
}

function Complete-Loading {
    param([string]$Status = "Done")
    
    $cursorPos = $Host.UI.RawUI.CursorPosition
    $cursorPos.X = 50
    $Host.UI.RawUI.CursorPosition = $cursorPos
    $checkmark = [char]0x2713
    Write-Host "[$checkmark] $Status" -ForegroundColor Green
}
# Step 1: Poetry
Show-Loading "[1/6] Installing Poetry and dependencies"
pip install --quiet poetry 2>&1 | Out-Null
poetry install --quiet 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Complete-Loading "Done"
} else {
    Complete-Loading "Warning"
}

# Step 2: pipx
Show-Loading "[2/6] Installing pipx"
pip install --quiet pipx 2>&1 | Out-Null

# Add Python Scripts to PATH for current session
$pythonScripts = python -c "import sysconfig; print(sysconfig.get_path('scripts'))"
if ($pythonScripts) {
    $env:PATH = "$pythonScripts;$env:PATH"
}

Complete-Loading "Done"

# Step 3: Clean old alfred installation
Show-Loading "[3/6] Cleaning old installation"

# Remove old pipx venv completely
$alfredVenv = "$env:USERPROFILE\pipx\venvs\alfred"
if (Test-Path $alfredVenv) {
    Remove-Item -Recurse -Force $alfredVenv 2>&1 | Out-Null
}

# Remove old binary
$alfredExe = "$env:USERPROFILE\.local\bin\alfred.exe"
if (Test-Path $alfredExe) {
    Remove-Item -Force $alfredExe 2>&1 | Out-Null
}

Complete-Loading "Done"

# Step 4: PATH setup
Show-Loading "[4/6] Configuring PATH"
python -m pipx ensurepath 2>&1 | Out-Null

$pipxBin = "$env:USERPROFILE\.local\bin"

# Add to system PATH
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$pipxBin*") {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$pipxBin", "User")
}

# Add to PowerShell profile
if (!(Test-Path $PROFILE)) {
    New-Item -Path $PROFILE -Type File -Force | Out-Null
}

$pathLine = 'if ($env:PATH -notlike "*$env:USERPROFILE\.local\bin*") { $env:PATH = "$env:USERPROFILE\.local\bin;$env:PATH" }'
$profileContent = Get-Content $PROFILE -ErrorAction SilentlyContinue -Raw

if (!$profileContent -or $profileContent -notlike "*alfred installer*") {
    Add-Content $PROFILE "`n# Added by Alfred installer`n$pathLine"
}

Complete-Loading "Done"

# Step 5: Install Alfred (FRESH)
Show-Loading "[5/6] Installing Alfred"

$installOutput = python -m pipx install . 2>&1
$installExitCode = $LASTEXITCODE

if ($installExitCode -eq 0) {
    Complete-Loading "Done"
} else {
    Write-Host ""
    Write-Host ""
    Write-Host "  ERROR: Installation failed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Output:" -ForegroundColor Yellow
    Write-Host $installOutput
    Write-Host ""
    Read-Host "  Press Enter to exit"
    exit 1
}

# Step 6: Verify
Show-Loading "[6/6] Verifying"

if (Test-Path $alfredExe) {
    # Add to current session PATH
    $env:PATH = "$pipxBin;$env:PATH"
    
    Complete-Loading "Done"
} else {
    Write-Host ""
    Write-Host ""
    Write-Host "  ERROR: Binary not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Expected: $alfredExe" -ForegroundColor Yellow
    Write-Host ""
    python -m pipx list
    Write-Host ""
    Read-Host "  Press Enter to exit"
    exit 1
}


# Test command
try {
    alfred --version 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  SUCCESS! 'alfred' command works!" -ForegroundColor Green
        Write-Host ""
        Write-Host "  Get started:" -ForegroundColor Cyan
        Write-Host "    alfred setup" -ForegroundColor Yellow
        Write-Host "    alfred review yourfile.py" -ForegroundColor Yellow
    } else {
        throw "Not working"
    }
} catch {
    Write-Host ""
    Write-Host "Try: alfred setup" -ForegroundColor White
}
