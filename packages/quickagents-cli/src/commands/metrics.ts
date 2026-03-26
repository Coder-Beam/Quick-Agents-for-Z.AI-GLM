import fs from 'fs-extra';
import path from 'path';
import chalk from 'chalk';
import type { Command } from 'commander';

interface MetricsOptions {
  period: string;
  format: string;
}

interface SessionMetric {
  timestamp: string;
  session_id: string;
  git_branch: string;
  files_changed: number;
  commits_today: number;
  tasks_completed: number;
}

export async function metricsCommand(options: MetricsOptions, command: Command) {
  const cwd = process.cwd();
  const metricsDir = path.join(cwd, '.opencode/metrics');
  const sessionsLog = path.join(metricsDir, 'sessions.log');
  const coordinationMetrics = path.join(metricsDir, 'coordination.json');
  
  const periodDays = parseInt(options.period, 10) || 7;
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - periodDays);
  
  let metrics: {
    sessions: SessionMetric[];
    coordination: Record<string, unknown> | null;
  } = {
    sessions: [],
    coordination: null
  };
  
  // 读取会话指标
  if (await fs.pathExists(sessionsLog)) {
    const content = await fs.readFile(sessionsLog, 'utf-8');
    const lines = content.split('\n').filter(l => l.trim());
    
    for (const line of lines) {
      try {
        const metric: SessionMetric = JSON.parse(line);
        const metricDate = new Date(metric.timestamp);
        
        if (metricDate >= cutoffDate) {
          metrics.sessions.push(metric);
        }
      } catch {
        // 跳过无效行
      }
    }
  }
  
  // 读取协调指标
  if (await fs.pathExists(coordinationMetrics)) {
    metrics.coordination = await fs.readJson(coordinationMetrics);
  }
  
  if (options.format === 'json') {
    console.log(JSON.stringify(metrics, null, 2));
    return;
  }
  
  // 显示表格格式
  displayMetrics(metrics, periodDays);
}

function displayMetrics(metrics: { sessions: SessionMetric[]; coordination: Record<string, unknown> | null }, periodDays: number) {
  console.log(chalk.bold('\n项目指标 (最近 ' + periodDays + ' 天)\n'));
  
  console.log(chalk.bold('会话统计'));
  console.log(chalk.gray('─'.repeat(40)));
  
  const totalSessions = metrics.sessions.length;
  const totalCommits = metrics.sessions.reduce((sum, s) => sum + s.commits_today, 0);
  const totalTasksCompleted = metrics.sessions.reduce((sum, s) => sum + s.tasks_completed, 0);
  const totalFilesChanged = metrics.sessions.reduce((sum, s) => sum + s.files_changed, 0);
  
  console.log('  会话数: ' + chalk.cyan(totalSessions.toString()));
  console.log('  提交数: ' + chalk.cyan(totalCommits.toString()));
  console.log('  完成任务: ' + chalk.cyan(totalTasksCompleted.toString()));
  console.log('  修改文件: ' + chalk.cyan(totalFilesChanged.toString()));
  
  if (totalSessions > 0) {
    console.log('\n' + chalk.bold('每日活动'));
    console.log(chalk.gray('─'.repeat(40)));
    
    // 按日期分组
    const byDate: Record<string, SessionMetric[]> = {};
    for (const session of metrics.sessions) {
      const date = session.timestamp.split('T')[0];
      if (!byDate[date]) {
        byDate[date] = [];
      }
      byDate[date].push(session);
    }
    
    const sortedDates = Object.keys(byDate).sort().reverse().slice(0, 7);
    
    for (const date of sortedDates) {
      const sessions = byDate[date];
      const bar = '█'.repeat(Math.min(sessions.length, 10)) + '░'.repeat(10 - Math.min(sessions.length, 10));
      console.log('  ' + date + ' ' + chalk.cyan(bar) + ' ' + sessions.length + ' 会话');
    }
  }
  
  if (metrics.coordination) {
    console.log('\n' + chalk.bold('协调统计'));
    console.log(chalk.gray('─'.repeat(40)));
    console.log('  ' + chalk.dim(JSON.stringify(metrics.coordination, null, 2)));
  }
  
  // 显示趋势
  if (metrics.sessions.length >= 2) {
    console.log('\n' + chalk.bold('趋势分析'));
    console.log(chalk.gray('─'.repeat(40)));
    
    const halfPoint = Math.floor(metrics.sessions.length / 2);
    const recent = metrics.sessions.slice(0, halfPoint);
    const earlier = metrics.sessions.slice(halfPoint);
    
    const recentAvg = recent.reduce((s, m) => s + m.tasks_completed, 0) / recent.length;
    const earlierAvg = earlier.reduce((s, m) => s + m.tasks_completed, 0) / earlier.length;
    
    if (recentAvg > earlierAvg) {
      console.log('  任务完成: ' + chalk.green('↑ 上升趋势'));
    } else if (recentAvg < earlierAvg) {
      console.log('  任务完成: ' + chalk.red('↓ 下降趋势'));
    } else {
      console.log('  任务完成: ' + chalk.yellow('→ 稳定'));
    }
  }
}
