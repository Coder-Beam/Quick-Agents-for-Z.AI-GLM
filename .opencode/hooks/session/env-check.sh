#!/usr/bin/env bash
#
# Environment Check Hook
# 会话开始时检查环境配置
#
# 用法: ./env-check.sh
# 返回: 0 = 环境正常, 1 = 环境异常
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

log_section() {
    echo -e "\n${BLUE}════════════════════════════════════════${NC}"
    echo -e "${BLUE} $1 ${NC}"
    echo -e "${BLUE}════════════════════════════════════════${NC}\n"
}

check_node() {
    if command -v node &> /dev/null; then
        local version
        version=$(node --version)
        log_info "Node.js: $version"
        return 0
    else
        log_warn "Node.js: 未安装"
        return 1
    fi
}

check_npm() {
    if command -v npm &> /dev/null; then
        local version
        version=$(npm --version)
        log_info "npm: $version"
        return 0
    else
        log_warn "npm: 未安装"
        return 1
    fi
}

check_git() {
    if command -v git &> /dev/null; then
        local version
        version=$(git --version | cut -d' ' -f3)
        log_info "Git: $version"
        return 0
    else
        log_warn "Git: 未安装"
        return 1
    fi
}

check_python() {
    if command -v python3 &> /dev/null; then
        local version
        version=$(python3 --version | cut -d' ' -f2)
        log_info "Python: $version"
        return 0
    elif command -v python &> /dev/null; then
        local version
        version=$(python --version | cut -d' ' -f2)
        log_info "Python: $version"
        return 0
    else
        log_warn "Python: 未安装"
        return 1
    fi
}

check_project_dependencies() {
    if [ -f "package.json" ] && [ ! -d "node_modules" ]; then
        log_warn "检测到 package.json 但 node_modules 不存在"
        log_info "建议运行: npm install 或 pnpm install"
        return 1
    fi
    return 0
}

check_env_files() {
    local warnings=0
    
    if [ -f ".env.example" ] && [ ! -f ".env" ]; then
        log_warn "检测到 .env.example 但 .env 不存在"
        log_info "建议: cp .env.example .env 并配置环境变量"
        warnings=$((warnings + 1))
    fi
    
    return $warnings
}

check_git_status() {
    if [ -d ".git" ]; then
        local branch
        branch=$(git branch --show-current 2>/dev/null || echo "unknown")
        log_info "当前分支: $branch"
        
        local uncommitted
        uncommitted=$(git status --porcelain 2>/dev/null | wc -l)
        if [ "$uncommitted" -gt 0 ]; then
            log_warn "有 $uncommitted 个未提交的更改"
        fi
    fi
    return 0
}

check_opencode_config() {
    if [ -d ".opencode" ]; then
        log_info "OpenCode 配置目录存在"
        
        if [ -f ".opencode/agents" ]; then
            local agent_count
            agent_count=$(ls -1 .opencode/agents/*.md 2>/dev/null | wc -l)
            log_info "已配置 $agent_count 个 Agent"
        fi
        
        if [ -f ".opencode/skills" ]; then
            local skill_count
            skill_count=$(ls -1d .opencode/skills/*/ 2>/dev/null | wc -l)
            log_info "已配置 $skill_count 个 Skill"
        fi
    else
        log_warn ".opencode 目录不存在"
    fi
    return 0
}

main() {
    local start_time
    start_time=$(date +%s)
    
    log_section "QuickAgents 环境检查"
    
    local errors=0
    local warnings=0
    
    log_section "系统工具"
    check_node || warnings=$((warnings + 1))
    check_npm || warnings=$((warnings + 1))
    check_git || warnings=$((warnings + 1))
    check_python || true  # Python 可选
    
    log_section "项目配置"
    check_project_dependencies || warnings=$((warnings + 1))
    check_env_files || warnings=$((warnings + 1))
    check_git_status
    check_opencode_config
    
    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    log_section "检查结果"
    echo -e "  检查时间: ${duration}s"
    echo -e "  警告数: ${YELLOW}${warnings}${NC}"
    echo -e "  错误数: ${RED}${errors}${NC}"
    
    if [ $errors -gt 0 ]; then
        log_error "环境检查失败 ✗"
        exit 1
    elif [ $warnings -gt 0 ]; then
        log_warn "环境检查通过（有警告） ⚠"
        exit 0
    else
        log_info "环境检查通过 ✓"
        exit 0
    fi
}

main "$@"
