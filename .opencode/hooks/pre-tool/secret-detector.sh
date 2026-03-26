#!/usr/bin/env bash
#
# Secret Detector Hook
# 检测敏感信息泄露
#
# 用法: ./secret-detector.sh <file_path> [content]
# 返回: 0 = 通过, 1 = 发现敏感信息
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [SECRET-DETECTOR] $1"
}

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 敏感信息正则模式
SECRET_PATTERNS=(
    # API Keys
    "api[_-]?key['\"]?\s*[:=]\s*['\"][a-zA-Z0-9_\-]{20,}['\"]"
    "apikey['\"]?\s*[:=]\s*['\"][a-zA-Z0-9_\-]{20,}['\"]"
    
    # AWS
    "AKIA[0-9A-Z]{16}"
    "aws[_-]?secret[_-]?access[_-]?key['\"]?\s*[:=]\s*['\"][a-zA-Z0-9/+=]{40}['\"]"
    
    # GitHub
    "ghp_[a-zA-Z0-9]{36}"
    "github[_-]?token['\"]?\s*[:=]\s*['\"][a-zA-Z0-9_\-]{35,}['\"]"
    
    # Generic Secrets
    "secret['\"]?\s*[:=]\s*['\"][a-zA-Z0-9_\-]{16,}['\"]"
    "password['\"]?\s*[:=]\s*['\"][^'\"]{8,}['\"]"
    "passwd['\"]?\s*[:=]\s*['\"][^'\"]{8,}['\"]"
    
    # Private Keys
    "-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"
    
    # Database URLs
    "(mysql|postgres|mongodb|redis)://[^:]+:[^@]+@[^/]+"
    
    # JWT Secrets
    "jwt[_-]?secret['\"]?\s*[:=]\s*['\"][a-zA-Z0-9_\-]{16,}['\"]"
)

# 白名单模式（允许的模式）
WHITELIST_PATTERNS=(
    "process\.env\."
    "import\.meta\.env\."
    "\$\{.*\}"
    "getenv\("
    "os\.environ"
    "config\.get"
    "\.env['\"]?\]"
)

detect_secrets() {
    local content="$1"
    local found_secrets=()
    
    for pattern in "${SECRET_PATTERNS[@]}"; do
        if echo "$content" | grep -qiE "$pattern"; then
            # 检查是否在白名单中
            local is_whitelisted=false
            for wpattern in "${WHITELIST_PATTERNS[@]}"; do
                if echo "$content" | grep -qiE "$wpattern"; then
                    is_whitelisted=true
                    break
                fi
            done
            
            if [ "$is_whitelisted" = false ]; then
                found_secrets+=("$pattern")
            fi
        fi
    done
    
    if [ ${#found_secrets[@]} -gt 0 ]; then
        log_error "检测到敏感信息模式:"
        for secret in "${found_secrets[@]}"; do
            echo "  - $secret"
        done
        return 1
    fi
    
    return 0
}

check_file() {
    local file_path="$1"
    
    if [ ! -f "$file_path" ]; then
        log_info "文件不存在或已删除: $file_path"
        return 0
    fi
    
    # 跳过二进制文件
    if file "$file_path" | grep -q "binary\|executable\|data"; then
        log_info "跳过二进制文件: $file_path"
        return 0
    fi
    
    # 跳过特定目录
    if [[ "$file_path" =~ (node_modules|\.git|dist|build|coverage) ]]; then
        return 0
    fi
    
    local content
    content=$(cat "$file_path" 2>/dev/null || echo "")
    
    if [ -z "$content" ]; then
        return 0
    fi
    
    if detect_secrets "$content"; then
        log_info "文件检查通过: $file_path"
        return 0
    else
        log_error "文件包含敏感信息: $file_path"
        return 1
    fi
}

main() {
    log "开始敏感信息检测..."
    
    local exit_code=0
    
    if [ -n "$1" ]; then
        # 检查指定文件
        check_file "$1" || exit_code=1
    else
        # 检查暂存的文件
        if command -v git &> /dev/null; then
            local files
            files=$(git diff --cached --name-only --diff-filter=ACM 2>/dev/null || echo "")
            
            if [ -n "$files" ]; then
                while IFS= read -r file; do
                    check_file "$file" || exit_code=1
                done <<< "$files"
            else
                log_info "没有暂存的文件需要检查"
            fi
        fi
    fi
    
    if [ $exit_code -eq 0 ]; then
        log_info "敏感信息检测通过 ✓"
    else
        log_error "敏感信息检测失败 ✗"
        echo ""
        echo "建议操作:"
        echo "  1. 使用环境变量存储敏感信息"
        echo "  2. 将敏感文件添加到 .gitignore"
        echo "  3. 使用 .env 文件并确保已忽略"
    fi
    
    exit $exit_code
}

main "$@"
