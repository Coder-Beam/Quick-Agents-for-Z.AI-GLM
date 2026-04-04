-- ==================== AuditGuard 迁移 ====================
-- 版本: 003
-- 名称: audit_tables
-- 说明: 创建审计日志、问责记录、学习经验三张核心表

-- 审计日志（反 DarkCode 核心）
CREATE TABLE IF NOT EXISTS audit_log (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    task_id TEXT,
    file_path TEXT NOT NULL,
    change_type TEXT NOT NULL,
    diff_content TEXT,
    lines_added INTEGER DEFAULT 0,
    lines_removed INTEGER DEFAULT 0,
    tool_name TEXT,
    quality_status TEXT DEFAULT 'PENDING',
    summary TEXT,
    created_at REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_log_session ON audit_log(session_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_task ON audit_log(task_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_file ON audit_log(file_path);
CREATE INDEX IF NOT EXISTS idx_audit_log_time ON audit_log(created_at);

-- 问责记录
CREATE TABLE IF NOT EXISTS audit_issues (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    task_id TEXT,
    issue_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    file_path TEXT,
    line_number INTEGER,
    check_name TEXT,
    error_code TEXT,
    error_message TEXT NOT NULL,
    root_cause TEXT,
    status TEXT DEFAULT 'OPEN',
    created_at REAL NOT NULL,
    resolved_at REAL,
    fix_strategy TEXT,
    fix_commit TEXT,
    occurrence_count INTEGER DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_audit_issues_session ON audit_issues(session_id);
CREATE INDEX IF NOT EXISTS idx_audit_issues_task ON audit_issues(task_id);
CREATE INDEX IF NOT EXISTS idx_audit_issues_status ON audit_issues(status);
CREATE INDEX IF NOT EXISTS idx_audit_issues_severity ON audit_issues(severity);
CREATE INDEX IF NOT EXISTS idx_audit_issues_type ON audit_issues(issue_type);

-- 学习经验
CREATE TABLE IF NOT EXISTS audit_lessons (
    id TEXT PRIMARY KEY,
    issue_id TEXT REFERENCES audit_issues(id),
    lesson_type TEXT NOT NULL,
    category TEXT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    trigger_pattern TEXT,
    prevention_tip TEXT,
    created_at REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_lessons_type ON audit_lessons(lesson_type);
CREATE INDEX IF NOT EXISTS idx_audit_lessons_category ON audit_lessons(category);
CREATE INDEX IF NOT EXISTS idx_audit_lessons_issue ON audit_lessons(issue_id);
