import fs from 'fs-extra';
import path from 'path';
import chalk from 'chalk';
import ora from 'ora';
import type { Command } from 'commander';

interface StartOptions {
  agent?: string;
  task?: string;
}

export async function startCommand(options: StartOptions, command: Command) {
  const spinner = ora('启动 QuickAgents 会话...').start();
  
  try {
    const cwd = process.cwd();
    const opencodeDir = path.join(cwd, '.opencode');
    
    // 检查是否已初始化
    if (!await fs.pathExists(opencodeDir)) {
      spinner.fail(chalk.red('项目未初始化'));
      console.log(chalk.yellow('请先运行 ') + chalk.cyan('qa init') + chalk.yellow(' 初始化项目'));
      process.exit(1);
    }
    
    // 读取项目配置
    const configPath = path.join(opencodeDir, 'opencode.json');
    const config = await fs.readJson(configPath);
    
    spinner.succeed(chalk.green('会话已准备就绪'));
    
    // 显示会话信息
    console.log('\n' + chalk.bold('项目信息:'));
    console.log('  名称: ' + chalk.cyan(config.project?.name || path.basename(cwd)));
    console.log('  类型: ' + chalk.cyan(config.project?.type || 'auto-detect'));
    
    // 显示可用代理
    const agentsDir = path.join(opencodeDir, 'agents');
    const agents = await fs.readdir(agentsDir).catch(() => []);
    const agentFiles = agents.filter(f => f.endsWith('.md'));
    
    if (agentFiles.length > 0) {
      console.log('\n' + chalk.bold('可用代理 (' + agentFiles.length + '):'));
      for (const agent of agentFiles.slice(0, 5)) {
        console.log('  - ' + chalk.cyan(agent.replace('.md', '')));
      }
      if (agentFiles.length > 5) {
        console.log('  - ' + chalk.gray('... 以及 ' + (agentFiles.length - 5) + ' 个更多'));
      }
    }
    
    // 显示当前任务
    if (options.task) {
      console.log('\n' + chalk.bold('恢复任务: ') + chalk.yellow(options.task));
    } else {
      const tasksPath = path.join(cwd, 'Docs/TASKS.md');
      if (await fs.pathExists(tasksPath)) {
        const tasksContent = await fs.readFile(tasksPath, 'utf-8');
        const pendingTasks = tasksContent.match(/- \[ \].+/g) || [];
        if (pendingTasks.length > 0) {
          console.log('\n' + chalk.bold('待办任务:'));
          for (const task of pendingTasks.slice(0, 3)) {
            console.log('  ' + task);
          }
        }
      }
    }
    
    // 生成启动提示词
    console.log('\n' + chalk.bold('启动提示词:'));
    console.log(chalk.gray('─'.repeat(50)));
    console.log(chalk.green('启动QuickAgent'));
    console.log(chalk.gray('─'.repeat(50)));
    console.log('\n' + chalk.dim('将以上提示词发送给 OpenCode 开始工作'));
    
    // 如果指定了代理
    if (options.agent) {
      console.log('\n' + chalk.dim('或直接调用代理: @' + options.agent));
    }
    
  } catch (error) {
    spinner.fail(chalk.red('启动失败'));
    console.error(error);
    process.exit(1);
  }
}
