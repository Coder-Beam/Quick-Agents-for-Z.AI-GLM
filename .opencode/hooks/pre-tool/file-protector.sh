#!/usr/bin/env bash
#
# File Protector Hook
# 保护关键文件不被意外修改
#
# 用法: ./file-protector.sh <file_path> [operation]
# 返回: 0 = 允许, 1 = 拒绝
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
    echo -e "${RED}[ERROR]${NC] $1"
}

# 受保护文件模式
PROTECTED_PATTERNS=(
    ".env"
    ".env.local"
    ".env.*.local"
    "*.pem"
    "*.key"
    "*.p12"
    "*.pfx"
    "credentials.json"
    "secrets.json"
    "secrets.yaml"
    "secrets.yml"
    ".htpasswd"
    "id_rsa"
    "id_rsa.pub"
    "*.asc"
    "*.gpg"
)

# 受保护目录
PROTECTED_DIRS=(
    ".ssh"
    ".gnupg"
    "secrets"
    "credentials"
)

# 允许修改的例外（白名单）
ALLOWED_MODIFICATIONS=(
    ".env.example"
    ".env.template"
    "*.example"
    "*.sample"
    "*.template"
)

check_protected() {
    local file_path="$1"
    local filename
    filename=$(basename "$file_path")
    
    # 检查白名单
    for pattern in "${ALLOWED_MODIFICATIONS[@]}"; do
        if [[ "$filename" == $pattern ]]; then
            log_info "文件在白名单中，允许修改: $file_path"
            return 0
        fi
    done
    
    # 检查受保护模式
    for pattern in "${PROTECTED_PATTERNS[@]}"; do
        if [[ "$filename" == $pattern ]]; then
            log_error "文件受保护，禁止修改: $file_path"
            return 1
        fi
    done
    
    # 检查受保护目录
    for dir in "${PROTECTED_DIRS[@]}"; do
        if [[ "$file_path" == *"$dir"* ]]; then
            log_error "目录受保护，禁止修改: $file_path"
            return 1
        fi
    done
    
    return 0
}

main() {
    local file_path="${1:-}"
    local operation="${2:-write}"
    
    if [ -z "$file_path" ]; then
        log_info "未指定文件路径，跳过检查"
        exit 0
    fi
    
    log_info "检查文件保护: $file_path (操作: $operation)"
    
    if check_protected "$file_path"; then
        log_info "文件修改允许 ✓"
        exit 0
    else
        log_error "文件修改被拒绝 ✗"
        echo ""
        echo "受保护文件不能被修改。"
        echo "如果您确实需要修改此文件，请："
        echo "  1. 确认您了解修改的风险"
        echo "  2. 手动编辑文件"
        echo "  3. 或者更新 .opencode/hooks/hooks.json 中的白名单"
        exit 1
    fi
}

main "$@"
