#!/usr/bin/env bash
#
# Task Validator Hook
# 任务开始前验证
#
# 用法: ./task-validator.sh <task_id> [task_description]
# 返回: 0 = 验证通过, 1 = 验证失败
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

validate_task_id() {
    local task_id="$1"
    
    if [ -z "$task_id" ]; then
        log_error "任务ID不能为空"
        return 1
    fi
    
    # 检查任务ID格式 (T001, T-001, TASK-001 等)
    if [[ ! "$task_id" =~ ^[Tt][Aa]?[-_]?[0-9]{3,}$ ]]; then
        log_warn "任务ID格式建议: T001 或 TASK-001"
    fi
    
    return 0
}

validate_dependencies() {
    local task_id="$1"
    
    # 检查 MEMORY.md 中的依赖关系
    if [ -f "Docs/MEMORY.md" ]; then
        # 查找前置依赖
        if grep -q "前置依赖.*进行中" Docs/MEMORY.md 2>/dev/null; then
            log_warn "存在进行中的前置依赖"
            return 1
        fi
    fi
    
    return 0
}

validate_environment() {
    # 检查是否有未提交的更改
    if git diff --quiet 2>/dev/null; then
        log_info "工作目录干净"
    else
        log_warn "工作目录有未提交的更改"
    fi
    
    # 检查分支
    local branch
    branch=$(git branch --show-current 2>/dev/null || echo "unknown")
    log_info "当前分支: $branch"
    
    return 0
}

validate_task_exists() {
    local task_id="$1"
    
    # 检查 TASKS.md
    if [ -f "Docs/TASKS.md" ]; then
        if grep -q "$task_id" Docs/TASKS.md 2>/dev/null; then
            log_info "任务已定义: $task_id"
            return 0
        fi
    fi
    
    # 检查 .quickagents/boulder.json
    if [ -f ".quickagents/boulder.json" ]; then
        if grep -q "\"id\": \"$task_id\"" .quickagents/boulder.json 2>/dev/null; then
            log_info "任务已在进度追踪中: $task_id"
            return 0
        fi
    fi
    
    log_warn "任务未在 TASKS.md 或 boulder.json 中找到"
    return 0  # 不阻止任务开始
}

main() {
    local task_id="${1:-}"
    local task_description="${2:-}"
    
    log_info "验证任务: $task_id"
    [ -n "$task_description" ] && log_info "描述: $task_description"
    
    local exit_code=0
    
    # 验证任务ID
    if ! validate_task_id "$task_id"; then
        exit_code=1
    fi
    
    # 验证任务存在
    if ! validate_task_exists "$task_id"; then
        exit_code=1
    fi
    
    # 验证依赖
    if ! validate_dependencies "$task_id"; then
        exit_code=1
    fi
    
    # 验证环境
    validate_environment
    
    if [ $exit_code -eq 0 ]; then
        log_info "任务验证通过 ✓"
    else
        log_error "任务验证失败 ✗"
    fi
    
    exit $exit_code
}

main "$@"
