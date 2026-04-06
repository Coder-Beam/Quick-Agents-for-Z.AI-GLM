# QuickAgents One-Line Installer for Windows PowerShell
#
# Usage:
#   iwr -useb https://raw.githubusercontent.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/main/scripts/install.ps1 | iex
#   iwr -useb ... | iex -WithUiUx
#
# Options:
#   -WithUiUx      Include ui-ux-pro-max skill (~410KB, for web/mobile projects)
#   -WithBrowser   Include browser-devtools skill
#   -Minimal       Minimal installation (core files only)
#   -Check         Only check prerequisites, don't install
#   -Uninstall     Remove QuickAgents from current project
#   -Help          Show this help message

param(
    [switch]$WithUiUx,
    [switch]$WithBrowser,
    [switch]$Minimal,
    [switch]$Check,
    [switch]$Uninstall,
    [switch]$Help
)

# Colors for output
$Red = "`e[0;31m"
$Green = "`e[0;32m"
$Yellow = "`e[33m"
$Blue = "`e[34m"
$ResetColor = "`e[0m"

# Show help
if ($Help) {
    Write-Host "QuickAgents One-Line Installer for Windows" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: iwr -useb URL | iex [options]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -WithUiUx      Include ui-ux-pro-max skill (~410KB)"
    Write-Host "  -WithBrowser   Include browser-devtools skill"
    Write-Host "  -Minimal       Minimal installation (core files only)"
    Write-Host "  -Check         Only check prerequisites, don't install"
    Write-Host "  -Uninstall     Remove QuickAgents from current project"
    Write-Host "  -Help          Show this help message"
    exit 0
}

# Uninstall
if ($Uninstall) {
    Write-Host "`n$Yellow[3/4] Uninstalling QuickAgents...$ResetColor" -ForegroundColor Yellow
    
    $dirs = @(".opencode", ".quickagents", "Docs")
    $files = @("AGENTS.md", "opencode.json", "VERSION.md", "quickagents.json")
    
    foreach ($dir in $dirs) {
        if (Test-Path $dir) {
            Remove-Item -Path $dir -Recurse -Force
            Write-Host "  $Green[OK]$ResetColor Removed $dir" -ForegroundColor Green
        }
    }
    
    foreach ($file in $files) {
        if (Test-Path $file) {
            Remove-Item -Path $file -Force
            Write-Host "  $Green[OK]$ResetColor Removed $file" -ForegroundColor Green
        }
    }
    
    Write-Host "`n$Green[OK] QuickAgents has been removed from this project$ResetColor" -ForegroundColor Green
    exit 0
}

# Check only mode
if ($Check) {
    Write-Host "`n$Blue[1/4] Checking prerequisites...$ResetColor" -ForegroundColor Cyan
    
    # Check Python
    $python = Get-Command python -ErrorAction SilentlyContinue
    $python3 = Get-Command python3 -ErrorAction SilentlyContinue
    
    if ($python) {
        $version = & python --version 2>&1
        Write-Host "  $Green[OK]$ResetColor python: $version" -ForegroundColor Green
    } elseif ($python3) {
        $version = & python3 --version 2>&1
        Write-Host "  $Green[OK]$ResetColor python3: $version" -ForegroundColor Green
    } else {
        Write-Host "  $Red[FAIL]$ResetColor Python not found" -ForegroundColor Red
        Write-Host "  Install from: https://www.python.org/downloads/" -ForegroundColor Yellow
        exit 1
    }
    
    # Check pip
    $pip = Get-Command pip -ErrorAction SilentlyContinue
    if ($pip) {
        Write-Host "  $Green[OK]$ResetColor pip available" -ForegroundColor Green
    } else {
        Write-Host "  $Red[FAIL]$ResetColor pip not found" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "`n$Green[OK] All prerequisites met$ResetColor" -ForegroundColor Green
    exit 0
}

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "    QuickAgents One-Line Installer" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# 1. Check prerequisites
Write-Host "`n$Blue[1/4] Checking prerequisites...$ResetColor" -ForegroundColor Cyan

# Check Python
$python = Get-Command python -ErrorAction SilentlyContinue
$python3 = Get-Command python3 -ErrorAction SilentlyContinue
$pythonCmd = $null

if ($python) {
    $pythonCmd = "python"
} elseif ($python3) {
    $pythonCmd = "python3"
} else {
    Write-Host "  $Red[FAIL]$ResetColor Python not found" -ForegroundColor Red
    Write-Host "  Please install Python 3.9+ from:" -ForegroundColor Yellow
    Write-Host "  - https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "  - winget install Python.Python.3.12" -ForegroundColor Yellow
    Write-Host "  - scoop install python" -ForegroundColor Yellow
    exit 1
}

$version = & $pythonCmd --version 2>&1
Write-Host "  $Green[OK]$ResetColor Python: $version" -ForegroundColor Green

# Check pip
$pip = Get-Command pip -ErrorAction SilentlyContinue
if (-not $pip) {
    Write-Host "  $Red[FAIL]$ResetColor pip not found" -ForegroundColor Red
    exit 1
}
Write-Host "  $Green[OK]$ResetColor pip available" -ForegroundColor Green

# Check git (optional)
$git = Get-Command git -ErrorAction SilentlyContinue
if ($git) {
    Write-Host "  $Green[OK]$ResetColor git available" -ForegroundColor Green
} else {
    Write-Host "  $Yellow[WARN]$ResetColor git not found (optional)" -ForegroundColor Yellow
}

# 2. Install Python package
Write-Host "`n$Blue[2/4] Installing QuickAgents Python package...$ResetColor" -ForegroundColor Cyan

$pipArgs = @("install", "quickagents", "--upgrade")
$result = & pip @pipArgs 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "  $Red[FAIL]$ResetColor Installation failed" -ForegroundColor Red
    Write-Host $result
    exit 1
}
Write-Host "  $Green[OK]$ResetColor pip install quickagents completed" -ForegroundColor Green

# 3. Initialize project
Write-Host "`n$Blue[3/4] Initializing project...$ResetColor" -ForegroundColor Cyan

$initArgs = @("init")
if ($WithUiUx) { $initArgs += "--with-ui-ux" }
if ($WithBrowser) { $initArgs += "--with-browser" }
if ($Minimal) { $initArgs += "--minimal" }

$result = & $pythonCmd -m quickagents.cli.main @initArgs 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "  $Red[FAIL]$ResetColor Initialization failed" -ForegroundColor Red
    Write-Host $result
    exit 1
}
Write-Host $result

# 4. Verify installation
Write-Host "`n$Blue[4/4] Verifying installation...$ResetColor" -ForegroundColor Cyan

# Check CLI
$qka = Get-Command qka -ErrorAction SilentlyContinue
if ($qka) {
    $qaVersion = & qka version 2>&1 | Select-Object -First 1
    Write-Host "  $Green[OK]$ResetColor qka: $qaVersion" -ForegroundColor Green
} else {
    Write-Host "  $Yellow[WARN]$ResetColor qka command not in PATH" -ForegroundColor Yellow
    Write-Host "  You may need to restart your terminal" -ForegroundColor Yellow
}

# Check essential files
$essentialFiles = @("AGENTS.md", "opencode.json", ".opencode\plugins\quickagents.ts")
$allOk = $true
foreach ($file in $essentialFiles) {
    if (Test-Path $file) {
        Write-Host "  $Green[OK]$ResetColor $file" -ForegroundColor Green
    } else {
        Write-Host "  $Red[FAIL]$ResetColor $file (missing)" -ForegroundColor Red
        $allOk = $false
    }
}

if (-not $allOk) {
    Write-Host "`n$Yellow[WARN] Some files are missing. Run 'qka init --force' to fix$ResetColor" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "$Green===============================================$ResetColor" -ForegroundColor Green
Write-Host "$Green     Installation Complete!$ResetColor" -ForegroundColor Green
Write-Host "$Green===============================================$ResetColor" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Open your project in OpenCode"
Write-Host "  2. Send: $Cyan'启动QuickAgent'$ResetColor"
Write-Host "  3. Follow the interactive prompts"
Write-Host ""
Write-Host "Documentation: https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM" -ForegroundColor Cyan
