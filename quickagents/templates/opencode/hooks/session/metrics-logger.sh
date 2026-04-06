#!/usr/bin/env bash
#
# Metrics Logger Hook
# 会话结束时记录指标
#
# 用法: ./metrics-logger.sh [session_id]
# 返回: 0 = 成功
#

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# 指标存储目录
METRICS_DIR=".opencode/metrics"
LOG_FILE="$METRICS_DIR/sessions.log"

ensure_metrics_dir() {
    mkdir -p "$METRICS_DIR"
}

get_session_metrics() {
    local session_id="${1:-$(date +%Y%m%d_%H%M%S)}"
    
    # 收集指标
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    local git_branch
    git_branch=$(git branch --show-current 2>/dev/null || echo "unknown")
    
    local files_changed
    files_changed=$(git diff --name-only 2>/dev/null | wc -l)
    
    local commits_today
    commits_today=$(git log --since="midnight" --oneline 2>/dev/null | wc -l)
    
    local tasks_completed
    if [ -f ".quickagents/boulder.json" ]; then
        tasks_completed=$(grep -c '"status": "completed"' .quickagents/boulder.json 2>/dev/null || echo "0")
    else
        tasks_completed=0
    fi
    
    # 输出 JSON 格式的指标
    cat <<EOF
{
  "session_id": "$session_id",
  "timestamp": "$timestamp",
  "git_branch": "$git_branch",
  "files_changed": $files_changed,
  "commits_today": $commits_today,
  "tasks_completed": $tasks_completed
}
EOF
}

append_to_log() {
    local metrics="$1"
    echo "$metrics" >> "$LOG_FILE"
}

generate_summary() {
    if [ ! -f "$LOG_FILE" ]; then
        echo "暂无历史记录"
        return
    fi
    
    local total_sessions
    total_sessions=$(wc -l < "$LOG_FILE")
    
    local today_sessions
    today_sessions=$(grep -c "$(date +%Y-%m-%d)" "$LOG_FILE" 2>/dev/null || echo "0")
    
    log_info "会话统计:"
    echo "  - 今日会话: $today_sessions"
    echo "  - 总会话数: $total_sessions"
}

main() {
    local session_id="${1:-}"
    
    ensure_metrics_dir
    
    log_info "记录会话指标..."
    
    local metrics
    metrics=$(get_session_metrics "$session_id")
    
    append_to_log "$metrics"
    
    log_info "指标已记录到: $LOG_FILE"
    
    echo ""
    log_debug "本次会话指标:"
    echo "$metrics" | head -10
    
    echo ""
    generate_summary
    
    exit 0
}

main "$@"
