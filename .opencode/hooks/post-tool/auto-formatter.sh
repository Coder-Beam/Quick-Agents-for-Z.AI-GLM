#!/usr/bin/env bash
#
# Auto Formatter Hook
# 自动格式化代码
#
# 用法: ./auto-formatter.sh <file_path>
# 返回: 0 = 成功
#

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# 检测项目使用的格式化工具
detect_formatter() {
    local file_path="$1"
    local ext="${file_path##*.}"
    
    # 检查 prettier
    if [ -f "node_modules/.bin/prettier" ] || command -v prettier &> /dev/null; then
        echo "prettier"
        return 0
    fi
    
    # 检查特定语言的格式化工具
    case "$ext" in
        ts|tsx|js|jsx)
            if [ -f ".eslintrc.js" ] || [ -f ".eslintrc.json" ] || [ -f ".eslintrc.yaml" ]; then
                echo "eslint"
                return 0
            fi
            ;;
        py)
            if command -v black &> /dev/null; then
                echo "black"
                return 0
            elif command -v autopep8 &> /dev/null; then
                echo "autopep8"
                return 0
            fi
            ;;
        go)
            if command -v gofmt &> /dev/null; then
                echo "gofmt"
                return 0
            fi
            ;;
        rs)
            if command -v rustfmt &> /dev/null; then
                echo "rustfmt"
                return 0
            fi
            ;;
        java)
            if command -v google-java-format &> /dev/null; then
                echo "google-java-format"
                return 0
            fi
            ;;
    esac
    
    echo "none"
}

format_with_prettier() {
    local file_path="$1"
    
    if [ -f "node_modules/.bin/prettier" ]; then
        node_modules/.bin/prettier --write "$file_path" 2>/dev/null
    elif command -v prettier &> /dev/null; then
        prettier --write "$file_path" 2>/dev/null
    fi
}

format_with_eslint() {
    local file_path="$1"
    
    if [ -f "node_modules/.bin/eslint" ]; then
        node_modules/.bin/eslint --fix "$file_path" 2>/dev/null || true
    elif command -v eslint &> /dev/null; then
        eslint --fix "$file_path" 2>/dev/null || true
    fi
}

format_file() {
    local file_path="$1"
    local ext="${file_path##*.}"
    
    # 跳过不需要格式化的文件
    case "$ext" in
        md|txt|json|yaml|yml|toml)
            # 这些文件用 prettier 格式化
            ;;
        ts|tsx|js|jsx|css|scss|less|html|vue|svelte)
            # 这些文件需要格式化
            ;;
        *)
            log_debug "跳过文件类型: .$ext"
            return 0
            ;;
    esac
    
    # 跳过特定目录
    if [[ "$file_path" =~ (node_modules|\.git|dist|build|coverage|.next|.nuxt) ]]; then
        return 0
    fi
    
    local formatter
    formatter=$(detect_formatter "$file_path")
    
    case "$formatter" in
        prettier)
            log_info "使用 Prettier 格式化: $file_path"
            format_with_prettier "$file_path"
            ;;
        eslint)
            log_info "使用 ESLint 格式化: $file_path"
            format_with_eslint "$file_path"
            ;;
        black)
            log_info "使用 Black 格式化: $file_path"
            black "$file_path" 2>/dev/null
            ;;
        gofmt)
            log_info "使用 gofmt 格式化: $file_path"
            gofmt -w "$file_path" 2>/dev/null
            ;;
        rustfmt)
            log_info "使用 rustfmt 格式化: $file_path"
            rustfmt "$file_path" 2>/dev/null
            ;;
        none)
            log_debug "未找到格式化工具"
            ;;
    esac
    
    return 0
}

main() {
    local file_path="${1:-}"
    
    if [ -z "$file_path" ]; then
        log_info "未指定文件路径，跳过格式化"
        exit 0
    fi
    
    if [ ! -f "$file_path" ]; then
        log_info "文件不存在: $file_path"
        exit 0
    fi
    
    format_file "$file_path"
    
    log_info "自动格式化完成 ✓"
    exit 0
}

main "$@"
