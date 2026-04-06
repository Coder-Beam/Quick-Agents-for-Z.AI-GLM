#!/usr/bin/env bash
#
# Type Checker Hook
# TypeScript 类型检查
#
# 用法: ./type-checker.sh <file_path>
# 返回: 0 = 类型检查通过, 1 = 类型错误
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

# 检测 TypeScript 配置
detect_tsconfig() {
    if [ -f "tsconfig.json" ]; then
        echo "tsconfig.json"
        return 0
    elif [ -f "tsconfig.build.json" ]; then
        echo "tsconfig.build.json"
        return 0
    fi
    return 1
}

run_type_check() {
    local file_path="$1"
    local ext="${file_path##*.}"
    
    # 只检查 TypeScript 文件
    if [[ "$ext" != "ts" && "$ext" != "tsx" ]]; then
        log_info "非 TypeScript 文件，跳过类型检查"
        return 0
    fi
    
    # 跳过特定目录
    if [[ "$file_path" =~ (node_modules|\.git|dist|build|coverage) ]]; then
        return 0
    fi
    
    # 检查是否有 tsconfig
    if ! detect_tsconfig &>/dev/null; then
        log_warn "未找到 tsconfig.json，跳过类型检查"
        return 0
    fi
    
    # 运行类型检查
    local tsc_cmd=""
    
    if [ -f "node_modules/.bin/tsc" ]; then
        tsc_cmd="node_modules/.bin/tsc"
    elif command -v tsc &> /dev/null; then
        tsc_cmd="tsc"
    fi
    
    if [ -z "$tsc_cmd" ]; then
        log_warn "未找到 TypeScript 编译器"
        return 0
    fi
    
    log_info "运行类型检查: $file_path"
    
    # 使用 --noEmit 只检查类型，不生成文件
    if $tsc_cmd --noEmit 2>&1 | head -50; then
        log_info "类型检查通过 ✓"
        return 0
    else
        log_error "类型检查失败 ✗"
        return 1
    fi
}

main() {
    local file_path="${1:-}"
    
    if [ -z "$file_path" ]; then
        log_info "未指定文件路径，跳过类型检查"
        exit 0
    fi
    
    if [ ! -f "$file_path" ]; then
        log_info "文件不存在: $file_path"
        exit 0
    fi
    
    if run_type_check "$file_path"; then
        exit 0
    else
        exit 1
    fi
}

main "$@"
