#!/bin/bash
#
# QuickAgents One-Line Installer for macOS/Linux
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/main/scripts/install.sh | bash
#   curl -fsSL ... | bash -- --with-ui-ux
#
# Options:
#   --with-ui-ux      Include ui-ux-pro-max skill (~410KB, for web/mobile projects)
#   --with-browser    Include browser-devtools skill
#   --minimal         Minimal installation (core files only)
#   --check           Only check prerequisites, don't install
#   --uninstall       Remove QuickAgents from current project
#   --help            Show this help message

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
WITH_UI_UX=false
WITH_BROWSER=false
MINIMAL=false
CHECK_ONLY=false
UNINSTALL=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --with-ui-ux)
            WITH_UI_UX=true
            shift
            ;;
        --with-browser)
            WITH_BROWSER=true
            shift
            ;;
        --minimal)
            MINIMAL=true
            shift
            ;;
        --check)
            CHECK_ONLY=true
            shift
            ;;
        --uninstall)
            UNINSTALL=true
            shift
            ;;
        --help|-h)
            echo "QuickAgents One-Line Installer"
            echo ""
            echo "Usage: curl -fsSL URL | bash [options]"
            echo ""
            echo "Options:"
            echo "  --with-ui-ux    Include ui-ux-pro-max skill (~410KB)"
            echo "  --with-browser  Include browser-devtools skill"
            echo "  --minimal       Minimal installation (core files only)"
            echo "  --check         Only check prerequisites"
            echo "  --uninstall     Remove QuickAgents from current project"
            echo "  --help          Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}===============================================${NC}"
echo -e "${BLUE}     QuickAgents One-Line Installer${NC}"
echo -e "${BLUE}===============================================${NC}"
echo ""

# Uninstall mode
if [ "$UNINSTALL" = true ]; then
    echo -e "${YELLOW}Uninstalling QuickAgents...${NC}"
    if command -v qka &> /dev/null; then
        qka uninstall --force
    else
        echo -e "${YELLOW}qka command not found, removing files manually...${NC}"
        rm -rf .opencode AGENTS.md opencode.json .quickagents Docs
    fi
    echo -e "${GREEN}[OK] QuickAgents has been removed from this project${NC}"
    exit 0
fi

# Check prerequisites
echo -e "${BLUE}[1/4] Checking prerequisites...${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo -e "${RED}[FAIL] Python not found${NC}"
        echo "  Please install Python 3.9+ from https://www.python.org/downloads/"
        exit 1
    fi
    PYTHON_CMD="python"
else
    PYTHON_CMD="python3"
fi

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]); then
    echo -e "${RED}[FAIL] Python version too old: $PYTHON_VERSION${NC}"
    echo "  QuickAgents requires Python 3.9+"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} Python $PYTHON_VERSION"

# Check pip
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    echo -e "${RED}[FAIL] pip not found${NC}"
    exit 1
fi
PIP_CMD="pip3"
if ! command -v pip3 &> /dev/null; then
    PIP_CMD="pip"
fi
echo -e "  ${GREEN}✓${NC} pip available"

# Check git (optional but recommended)
if command -v git &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} git available"
else
    echo -e "  ${YELLOW}!${NC} git not found (optional)"
fi

if [ "$CHECK_ONLY" = true ]; then
    echo ""
    echo -e "${GREEN}[OK] All prerequisites met!${NC}"
    exit 0
fi

# Install QuickAgents
echo ""
echo -e "${BLUE}[2/4] Installing QuickAgents Python package...${NC}"

$PIP_CMD install --upgrade quickagents

if [ $? -ne 0 ]; then
    echo -e "${RED}[FAIL] Failed to install quickagents${NC}"
    exit 1
fi

echo -e "  ${GREEN}✓${NC} quickagents installed"

# Initialize project
echo ""
echo -e "${BLUE}[3/4] Initializing project...${NC}"

INIT_OPTS=""
if [ "$WITH_UI_UX" = true ]; then
    INIT_OPTS="$INIT_OPTS --with-ui-ux"
fi
if [ "$WITH_BROWSER" = true ]; then
    INIT_OPTS="$INIT_OPTS --with-browser"
fi
if [ "$MINIMAL" = true ]; then
    INIT_OPTS="$INIT_OPTS --minimal"
fi

qka init $INIT_OPTS

if [ $? -ne 0 ]; then
    echo -e "${RED}[FAIL] Failed to initialize project${NC}"
    exit 1
fi

# Verify installation
echo ""
echo -e "${BLUE}[4/4] Verifying installation...${NC}"

# Check CLI
if ! command -v qka &> /dev/null; then
    echo -e "${RED}[FAIL] qka command not found${NC}"
    echo "  You may need to restart your terminal or add Python bin to PATH"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} qka command available"

# Check version
QA_VERSION=$(qka version 2>&1 | head -1)
echo -e "  ${GREEN}✓${NC} $QA_VERSION"

# Check essential files
ESSENTIAL_FILES=("AGENTS.md" "opencode.json" ".opencode/plugins/quickagents.ts")
ALL_OK=true
for file in "${ESSENTIAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  ${GREEN}✓${NC} $file"
    else
        echo -e "  ${RED}✗${NC} $file (missing)"
        ALL_OK=false
    fi
done

if [ "$ALL_OK" = false ]; then
    echo -e "${YELLOW}[WARN] Some files are missing. Run 'qka init --force' to fix${NC}"
fi

echo ""
echo -e "${GREEN}===============================================${NC}"
echo -e "${GREEN}     Installation Complete!${NC}"
echo -e "${GREEN}===============================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Open your project in OpenCode"
echo "  2. Send: 启动QuickAgent"
echo "  3. Follow the interactive prompts"
echo ""
echo "Documentation: https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM"
echo ""
