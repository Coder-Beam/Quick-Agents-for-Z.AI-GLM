#!/usr/bin/env bash
#
# Desktop Notify Hook
# 桌面通知
#
# 用法: ./desktop-notify.sh <event_type> <message> [title]
# 返回: 0 = 成功
#

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# 默认配置
DEFAULT_TITLE="QuickAgents"
DEFAULT_SOUND=true

# 检测操作系统
detect_os() {
    case "$(uname -s)" in
        Darwin*)    echo "macos" ;;
        Linux*)     echo "linux" ;;
        MINGW*|MSYS*|CYGWIN*) echo "windows" ;;
        *)          echo "unknown" ;;
    esac
}

# macOS 通知
notify_macos() {
    local title="$1"
    local message="$2"
    local sound="$3"
    
    if command -v osascript &>/dev/null; then
        local sound_arg=""
        [ "$sound" = true ] && sound_arg='sound name "Glass"'
        
        osascript -e "display notification \"$message\" with title \"$title\" $sound_arg" 2>/dev/null
    elif command -v terminal-notifier &>/dev/null; then
        terminal-notifier -title "$title" -message "$message" 2>/dev/null
    fi
}

# Linux 通知
notify_linux() {
    local title="$1"
    local message="$2"
    
    if command -v notify-send &>/dev/null; then
        notify-send "$title" "$message" 2>/dev/null
    fi
}

# Windows 通知
notify_windows() {
    local title="$1"
    local message="$2"
    
    # PowerShell 通知
    if command -v powershell.exe &>/dev/null; then
        powershell.exe -Command "
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
            [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
            \$template = '<toast><visual><binding template=\"ToastText02\"><text id=\"1\">$title</text><text id=\"2\">$message</text></binding></visual></toast>'
            \$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
            \$xml.LoadXml(\$template)
            \$toast = [Windows.UI.Notifications.ToastNotification]::new(\$xml)
            [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('QuickAgents').Show(\$toast)
        " 2>/dev/null
    fi
}

# 获取事件图标
get_event_icon() {
    local event="$1"
    
    case "$event" in
        task_complete|task_completed) echo "✅" ;;
        error|fail|failed) echo "❌" ;;
        review_required|review) echo "🔍" ;;
        warning|warn) echo "⚠️" ;;
        success|done) echo "🎉" ;;
        *) echo "📢" ;;
    esac
}

main() {
    local event_type="${1:-info}"
    local message="${2:-}"
    local title="${3:-$DEFAULT_TITLE}"
    
    if [ -z "$message" ]; then
        log_warn "消息内容为空，跳过通知"
        exit 0
    fi
    
    # 添加事件图标
    local icon
    icon=$(get_event_icon "$event_type")
    title="$icon $title"
    
    local os
    os=$(detect_os)
    
    log_info "发送桌面通知: $message"
    
    case "$os" in
        macos)
            notify_macos "$title" "$message" "$DEFAULT_SOUND"
            ;;
        linux)
            notify_linux "$title" "$message"
            ;;
        windows)
            notify_windows "$title" "$message"
            ;;
        *)
            log_warn "不支持的操作系统，跳过通知"
            ;;
    esac
    
    exit 0
}

main "$@"
