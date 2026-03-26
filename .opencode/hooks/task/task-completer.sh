#!/usr/bin/env bash
#
# Task Completer Hook
# 任务完成后处理
#
# 用法: ./task-completer.sh <task_id> [status]
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

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

update_tasks_md() {
    local task_id="$1"
    local status="$2"
    
    if [ ! -f "Docs/TASKS.md" ]; then
        log_warn "Docs/TASKS.md 不存在"
        return 1
    fi
    
    # 更新任务状态
    if [ "$status" = "completed" ]; then
        local completion_date
        completion_date=$(date +%Y-%m-%d)
        
        # 使用 sed 更新状态（跨平台兼容）
        if sed --version &>/dev/null; then
            # GNU sed
            sed -i "s/\[ \] $task_id/[x] $task_id - 完成于 $completion_date/" Docs/TASKS.md
        else
            # BSD sed (macOS)
            sed -i "" "s/\[ \] $task_id/[x] $task_id - 完成于 $completion_date/" Docs/TASKS.md
        fi
        
        log_info "已更新 TASKS.md"
    fi
}

update_boulder() {
    local task_id="$1"
    local status="$2"
    
    if [ -f ".quickagents/boulder.json" ]; then
        log_debug "更新 boulder.json..."
        # 这里可以添加 JSON 更新逻辑
        # 需要 jq 工具
        if command -v jq &>/dev/null; then
            local tmp_file=".quickagents/boulder.json.tmp"
            jq --arg id "$task_id" --arg status "$status" \
                '(."active-tasks"[] | select(.id == $id) | .status) = $status' \
                .quickagents/boulder.json > "$tmp_file" && mv "$tmp_file" .quickagents/boulder.json
            log_info "已更新 boulder.json"
        fi
    fi
}

update_memory() {
    local task_id="$1"
    local status="$2"
    
    if [ -f "Docs/MEMORY.md" ]; then
        local timestamp
        timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
        
        # 添加完成记录到操作历史
        if grep -q "### 2.1 操作历史" Docs/MEMORY.md; then
            # 找到操作历史表格，添加新行
            local new_entry="| $timestamp | 任务完成: $task_id | $status | 自动记录 |"
            # 这里简化处理，实际可能需要更精确的插入位置
            log_debug "记录到 MEMORY.md"
        fi
    fi
}

generate_commit_reminder() {
    local task_id="$1"
    
    # 检查是否有未提交的更改
    if ! git diff --quiet 2>/dev/null; then
        log_warn "有未提交的更改"
        echo ""
        echo "建议提交命令:"
        echo "  git add ."
        echo "  git commit -m \"feat: 完成 $task_id\""
    fi
}

suggest_next_task() {
    if [ -f "Docs/TASKS.md" ]; then
        local next_task
        next_task=$(grep -m1 "\[ \]" Docs/TASKS.md 2>/dev/null || echo "")
        
        if [ -n "$next_task" ]; then
            echo ""
            log_info "下一个待办任务:"
            echo "  $next_task"
        fi
    fi
}

main() {
    local task_id="${1:-}"
    local status="${2:-completed}"
    
    log_info "任务完成处理: $task_id"
    
    # 更新任务文件
    update_tasks_md "$task_id" "$status"
    
    # 更新进度追踪
    update_boulder "$task_id" "$status"
    
    # 更新记忆
    update_memory "$task_id" "$status"
    
    # 生成提交提醒
    generate_commit_reminder "$task_id"
    
    # 建议下一个任务
    suggest_next_task
    
    log_info "任务完成处理结束 ✓"
    
    exit 0
}

main "$@"
