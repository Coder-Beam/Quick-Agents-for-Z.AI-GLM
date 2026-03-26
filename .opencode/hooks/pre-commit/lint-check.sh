#!/usr/bin/env bash
#
# Lint Check Hook
# Git 提交前代码质量检查
#
# 用法: ./lint-check.sh [--fix]
# 返回: 0 = 检查通过, 1 = 检查失败
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

FIX_MODE=false

if [ "$1" = "--fix" ]; then
    FIX_MODE=true
fi

# 检测 linter
detect_linter() {
    # ESLint
    if [ -f ".eslintrc.js" ] || [ -f ".eslintrc.json" ] || [ -f ".eslintrc.yaml" ] || [ -f ".eslintrc" ]; then
        echo "eslint"
        return 0
    fi
    
    # Pylint
    if [ -f ".pylintrc" ] || [ -f "pyproject.toml" ] && grep -q "pylint" pyproject.toml 2>/dev/null; then
        echo "pylint"
        return 0
    fi
    
    # Ruff
    if [ -f "ruff.toml" ] || [ -f "pyproject.toml" ] && grep -q "ruff" pyproject.toml 2>/dev/null; then
        echo "ruff"
        return 0
    fi
    
    # golangci-lint
    if [ -f ".golangci.yml" ] || [ -f ".golangci.yaml" ]; then
        echo "golangci-lint"
        return 0
    fi
    
    # clippy
    if [ -f "Cargo.toml" ] && command -v cargo-clippy &> /dev/null; then
        echo "clippy"
        return 0
    fi
    
    echo "none"
}

run_eslint() {
    local fix_flag=""
    if [ "$FIX_MODE" = true ]; then
        fix_flag="--fix"
    fi
    
    if [ -f "node_modules/.bin/eslint" ]; then
        node_modules/.bin/eslint $fix_flag --ext .js,.jsx,.ts,.tsx . 2>&1 | head -100
    elif command -v eslint &> /dev/null; then
        eslint $fix_flag --ext .js,.jsx,.ts,.tsx . 2>&1 | head -100
    fi
}

run_ruff() {
    local fix_flag=""
    if [ "$FIX_MODE" = true ]; then
        fix_flag="--fix"
    fi
    
    ruff check $fix_flag . 2>&1 | head -100
}

run_pylint() {
    pylint **/*.py 2>&1 | head -100
}

run_golangci_lint() {
    golangci-lint run ./... 2>&1 | head -100
}

run_clippy() {
    cargo clippy -- -D warnings 2>&1 | head -100
}

main() {
    log_info "开始代码检查..."
    
    local linter
    linter=$(detect_linter)
    
    if [ "$linter" = "none" ]; then
        log_warn "未检测到 linter，跳过检查"
        exit 0
    fi
    
    log_info "检测到 linter: $linter"
    
    if [ "$FIX_MODE" = true ]; then
        log_info "自动修复模式已启用"
    fi
    
    local exit_code=0
    
    case "$linter" in
        eslint)
            if ! run_eslint; then
                exit_code=1
            fi
            ;;
        ruff)
            if ! run_ruff; then
                exit_code=1
            fi
            ;;
        pylint)
            if ! run_pylint; then
                exit_code=1
            fi
            ;;
        golangci-lint)
            if ! run_golangci_lint; then
                exit_code=1
            fi
            ;;
        clippy)
            if ! run_clippy; then
                exit_code=1
            fi
            ;;
    esac
    
    if [ $exit_code -eq 0 ]; then
        log_info "代码检查通过 ✓"
    else
        log_error "代码检查失败 ✗"
        echo ""
        if [ "$FIX_MODE" = false ]; then
            echo "提示: 运行 ./lint-check.sh --fix 尝试自动修复"
        fi
    fi
    
    exit $exit_code
}

main "$@"
