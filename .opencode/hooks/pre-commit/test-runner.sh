#!/usr/bin/env bash
#
# Test Runner Hook
# Git 提交前运行测试
#
# 用法: ./test-runner.sh
# 返回: 0 = 测试通过, 1 = 测试失败
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# 检测测试框架
detect_test_runner() {
    # 检查 package.json 中的测试脚本
    if [ -f "package.json" ]; then
        if grep -q '"test"' package.json; then
            if [ -f "jest.config.js" ] || [ -f "jest.config.ts" ]; then
                echo "jest"
                return 0
            elif [ -f "vitest.config.ts" ] || [ -f "vitest.config.js" ]; then
                echo "vitest"
                return 0
            elif [ -f "mocha.opts" ] || [ -f ".mocharc.json" ]; then
                echo "mocha"
                return 0
            else
                echo "npm"
                return 0
            fi
        fi
    fi
    
    # 检查 pytest
    if [ -f "pytest.ini" ] || [ -f "setup.py" ] || [ -f "pyproject.toml" ]; then
        if command -v pytest &> /dev/null; then
            echo "pytest"
            return 0
        fi
    fi
    
    # 检查 go test
    if [ -f "go.mod" ]; then
        echo "go"
        return 0
    fi
    
    # 检查 cargo test
    if [ -f "Cargo.toml" ]; then
        echo "cargo"
        return 0
    fi
    
    echo "none"
}

run_jest_tests() {
    local changed_files="$1"
    
    if [ -f "node_modules/.bin/jest" ]; then
        # 只运行与修改文件相关的测试
        if [ -n "$changed_files" ]; then
            node_modules/.bin/jest --findRelatedTests --passWithNoTests $changed_files 2>&1
        else
            node_modules/.bin/jest --passWithNoTests 2>&1
        fi
    else
        npm test -- --passWithNoTests 2>&1
    fi
}

run_vitest_tests() {
    local changed_files="$1"
    
    if [ -f "node_modules/.bin/vitest" ]; then
        if [ -n "$changed_files" ]; then
            node_modules/.bin/vitest run --related $changed_files 2>&1
        else
            node_modules/.bin/vitest run 2>&1
        fi
    else
        npm test 2>&1
    fi
}

run_pytest() {
    python -m pytest --tb=short -q 2>&1
}

run_go_tests() {
    go test ./... -short 2>&1
}

run_cargo_tests() {
    cargo test --quiet 2>&1
}

get_changed_files() {
    git diff --cached --name-only --diff-filter=ACM 2>/dev/null | grep -E '\.(ts|tsx|js|jsx)$' | tr '\n' ' '
}

main() {
    log_info "开始运行测试..."
    
    local runner
    runner=$(detect_test_runner)
    
    if [ "$runner" = "none" ]; then
        log_warn "未检测到测试框架，跳过测试"
        exit 0
    fi
    
    log_info "检测到测试框架: $runner"
    
    local changed_files
    changed_files=$(get_changed_files)
    
    local exit_code=0
    
    case "$runner" in
        jest|vitest|npm)
            if ! run_jest_tests "$changed_files"; then
                exit_code=1
            fi
            ;;
        pytest)
            if ! run_pytest; then
                exit_code=1
            fi
            ;;
        go)
            if ! run_go_tests; then
                exit_code=1
            fi
            ;;
        cargo)
            if ! run_cargo_tests; then
                exit_code=1
            fi
            ;;
    esac
    
    if [ $exit_code -eq 0 ]; then
        log_info "测试通过 ✓"
    else
        log_error "测试失败 ✗"
        echo ""
        echo "请修复测试失败后再提交。"
        echo "可以使用 --no-verify 跳过此检查（不推荐）。"
    fi
    
    exit $exit_code
}

main "$@"
