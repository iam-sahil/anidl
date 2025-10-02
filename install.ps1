<#
Install script for Windows (PowerShell) to install the anidl package so the `anidl` command becomes available.

This script attempts the following, in order:
  1. If pipx is installed, use pipx to install the package from GitHub (recommended).
  2. Otherwise, install via `python -m pip install --user git+https://github.com/ctrlcat0x/anidl.git`.
     After a user install, the script will attempt to add the user Scripts directory to PATH using setx
     so the `anidl` console script becomes accessible in new shells.

Usage (single-line install via internet):
  irm https://raw.githubusercontent.com/ctrlcat0x/anidl/master/install.ps1 | iex

Or to use pipx explicitly (if installed locally):
  pipx install git+https://github.com/ctrlcat0x/anidl.git
#>

function Write-Info($m){ Write-Host $m -ForegroundColor Cyan }
function Write-Warn($m){ Write-Host $m -ForegroundColor Yellow }
function Write-Err($m){ Write-Host $m -ForegroundColor Red }

Write-Info "anidl installer starting..."

# prefer pipx if available
if (Get-Command pipx -ErrorAction SilentlyContinue) {
    Write-Info "pipx detected — installing via pipx (preferred)"
    try {
        pipx install --force "git+https://github.com/ctrlcat0x/anidl.git"
        Write-Info "Installed via pipx. You should be able to run: anidl search \"one piece\""
        exit 0
    } catch {
        Write-Warn "pipx install failed, falling back to user pip install. Error: $_"
    }
}

# ensure python is available
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Err "Python is not available on PATH. Please install Python 3.10+ and re-run this script."
    exit 1
}

Write-Info "Installing via pip (user install)..."
try {
    & python -m pip install --upgrade pip setuptools wheel
    & python -m pip install --user --upgrade "git+https://github.com/ctrlcat0x/anidl.git"
} catch {
    Write-Err "pip install failed: $_"
    exit 1
}

# detect if anidl command is available now
if (Get-Command anidl -ErrorAction SilentlyContinue) {
    Write-Info "Installation succeeded. You can now run: anidl search \"one piece\""
    exit 0
}

# Not on PATH — attempt to add user Scripts directory to PATH
Write-Info "'anidl' not found on PATH. Attempting to add user Scripts directory to PATH..."

$scripts = & python - <<'PY'
import site, os
print(os.path.join(site.USER_BASE, 'Scripts'))
PY

$scripts = $scripts.Trim()
Write-Info "User Scripts folder: $scripts"

if (-not (Test-Path $scripts)) {
    Write-Warn "Expected scripts folder does not exist. The package may have been installed elsewhere."
    Write-Info "You can try opening a new shell and running 'anidl'. If still not found, run:'python -m pip show anidl' to see install location."
    exit 0
}

# add to user PATH if not already present
if ($env:Path -notlike "*$scripts*") {
    Write-Info "Adding $scripts to user PATH using setx (applies to new shells)..."
    $new = "$($env:Path);$scripts"
    try {
        setx PATH $new | Out-Null
        Write-Info "Added $scripts to PATH. Open a new PowerShell to use the 'anidl' command."
    } catch {
        Write-Warn "Failed to update PATH automatically. Please add $scripts to your PATH manually."
    }
} else {
    Write-Info "$scripts already on PATH. Open a new shell and run 'anidl'"
}

Write-Info "Installation finished. If the 'anidl' command is still not found, open a new shell or run: python -m pip show anidl"