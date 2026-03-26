import fs from 'fs-extra';
import path from 'path';
import chalk from 'chalk';
import ora from 'ora';
import type { Command } from 'commander';

interface StatusOptions {
  json: boolean;
  detailed: boolean;
}

interface ProjectStatus {
  initialized: boolean;
  name: string;
  path: string;
  agents: { total: number; enabled: number };
  skills: { total: number; enabled: number };
  tasks: { total: number; completed: number; pending: number };
  coordination: { enabled: boolean };
  lastActivity: string | null;
}

export async function statusCommand(options: StatusOptions, command: Command) {
  const spinner = options.json ? null : ora('获取项目状态...').start();
  
  try {
    const cwd = process.cwd();
    const opencodeDir = path.join(cwd, '.opencode');
    
    const status: ProjectStatus = {
      initialized: await fs.pathExists(opencodeDir),
      name: path.basename(cwd),
      path: cwd,
      agents: { total: 0, enabled: 0 },
      skills: { total: 0, enabled: 0 },
      tasks: { total: 0, completed: 0, pending: 0 },
      coordination: { enabled: false },
      lastActivity: null
    };
    
    if (status.initialized) {
      // 统计代理
      const agentsDir = path.join(opencodeDir, 'agents');
      const agentFiles = await fs.readdir(agentsDir).catch(() => []);
      status.agents.total = agentFiles.filter(f => f.endsWith('.md')).length;
      status.agents.enabled = status.agents.total; // 假设所有都启用
      
      // 统计技能
      const skillsDir = path.join(opencodeDir, 'skills');
      const skillDirs = await fs.readdir(skillsDir).catch(() => []);
      status.skills.total = skillDirs.filter(d => !d.startsWith('.')).length;
      status.skills.enabled = status.skills.total;
      
      // 统计任务
      const tasksPath = path.join(cwd, 'Docs/TASKS.md');
      if (await fs.pathExists(tasksPath)) {
        const tasksContent = await fs.readFile(tasksPath, 'utf-8');
        status.tasks.completed = (tasksContent.match(/- \[x\]/g) || []).length;
        status.tasks.pending = (tasksContent.match(/- \[ \]/g) || []).length;
        status.tasks.total = status.tasks.completed + status.tasks.pending;
      }
      
      // 检查协调状态
      const coordPath = path.join(opencodeDir, 'config/coordination.json');
      if (await fs.pathExists(coordPath)) {
        const coordConfig = await fs.readJson(coordPath);
        status.coordination.enabled = coordConfig.enabled || false;
      }
      
      // 获取最后活动时间
      const memoryPath = path.join(cwd, 'Docs/MEMORY.md');
      if (await fs.pathExists(memoryPath)) {
        const stat = await fs.stat(memoryPath);
        status.lastActivity = stat.mtime.toISOString();
      }
    }
    
    if (spinner) spinner.succeed();
    
    if (options.json) {
      console.log(JSON.stringify(status, null, 2));
      return;
    }
    
    // 显示状态
    console.log('\n' + chalk.bold('QuickAgents 项目状态'));
    console.log(chalk.gray('─'.repeat(40)));
    
    console.log('\n' + chalk.bold('基本信息'));
    console.log('  名称: ' + chalk.cyan(status.name));
    console.log('  路径: ' + chalk.dim(status.path));
    console.log('  状态: ' + (status.initialized ? chalk.green('已初始化') : chalk.red('未初始化')));
    
    if (status.initialized) {
      console.log('\n' + chalk.bold('组件统计'));
      console.log('  代理: ' + chalk.cyan(status.agents.total.toString()));
      console.log('  技能: ' + chalk.cyan(status.skills.total.toString()));
      console.log('  多代理协调: ' + (status.coordination.enabled ? chalk.green('已启用') : chalk.gray('未启用')));
      
      console.log('\n' + chalk.bold('任务进度'));
      const progress = status.tasks.total > 0 
        ? Math.round((status.tasks.completed / status.tasks.total) * 100) 
        : 0;
      console.log('  完成: ' + chalk.green(status.tasks.completed.toString()));
      console.log('  待办: ' + chalk.yellow(status.tasks.pending.toString()));
      console.log('  进度: ' + chalk.cyan(progress + '%'));
      
      if (status.lastActivity) {
        const lastActive = new Date(status.lastActivity);
        console.log('\n' + chalk.bold('最后活动'));
        console.log('  ' + chalk.dim(lastActive.toLocaleString('zh-CN')));
      }
      
      if (options.detailed) {
        await showDetailedStatus(cwd, opencodeDir);
      }
    }
    
  } catch (error) {
    if (spinner) spinner.fail(chalk.red('获取状态失败'));
    console.error(error);
    process.exit(1);
  }
}

async function showDetailedStatus(cwd: string, opencodeDir: string) {
  // 显示代理列表
  const agentsDir = path.join(opencodeDir, 'agents');
  const agentFiles = await fs.readdir(agentsDir).catch(() => []);
  const agents = agentFiles.filter(f => f.endsWith('.md'));
  
  if (agents.length > 0) {
    console.log('\n' + chalk.bold('代理列表'));
    for (const agent of agents) {
      console.log('  - ' + agent.replace('.md', ''));
    }
  }
  
  // 显示技能列表
  const skillsDir = path.join(opencodeDir, 'skills');
  const skillDirs = await fs.readdir(skillsDir).catch(() => []);
  const skills = skillDirs.filter(d => !d.startsWith('.'));
  
  if (skills.length > 0) {
    console.log('\n' + chalk.bold('技能列表'));
    for (const skill of skills) {
      console.log('  - ' + skill);
    }
  }
}
