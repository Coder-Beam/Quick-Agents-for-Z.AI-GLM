import fs from 'fs-extra';
import path from 'path';
import chalk from 'chalk';
import ora from 'ora';
import type { Command } from 'commander';

interface WorkflowOptions {
  timeout?: string;
  dryRun?: boolean;
}

const CONFIG_PATH = 'config/quickagents.json';

export async function workflowCommand(action: string, name: string | undefined, options: WorkflowOptions, command: Command) {
  const cwd = process.cwd();
  const opencodeDir = path.join(cwd, '.opencode');
  const configPath = path.join(opencodeDir, CONFIG_PATH);
  
  switch (action) {
    case 'list':
      await listWorkflows(configPath);
      break;
    case 'run':
      await runWorkflow(configPath, name, options);
      break;
    case 'status':
      await workflowStatus(configPath, name);
      break;
    default:
      console.log(chalk.red('未知操作: ' + action));
      console.log(chalk.yellow('可用操作: list, run, status'));
  }
}

async function listWorkflows(configPath: string) {
  if (!await fs.pathExists(configPath)) {
    console.log(chalk.yellow('配置文件不存在'));
    console.log(chalk.dim('请先运行 /enable-coordination 启用多代理协调'));
    return;
  }
  
  const config = await fs.readJson(configPath);
  const coordination = config.coordination || {};
  
  if (!coordination.enabled) {
    console.log(chalk.yellow('多代理协调未启用'));
    console.log(chalk.dim('请先运行 /enable-coordination 启用'));
    return;
  }
  
  const workflows = coordination.workflows || {};
  const workflowNames = Object.keys(workflows);
  
  if (workflowNames.length === 0) {
    console.log(chalk.yellow('没有定义工作流'));
    return;
  }
  
  console.log(chalk.bold('\n可用工作流 (' + workflowNames.length + '):\n'));
  
  for (const [key, workflow] of Object.entries(workflows)) {
    const wf = workflow as { name?: string; description?: string; team?: string };
    console.log('  ' + chalk.cyan(key));
    console.log('    名称: ' + (wf.name || key));
    if (wf.description) {
      console.log('    描述: ' + chalk.dim(wf.description));
    }
    if (wf.team) {
      console.log('    团队: ' + chalk.dim(wf.team));
    }
  }
  
  console.log('\n' + chalk.dim('运行工作流: qa workflow run <name>'));
}

async function runWorkflow(configPath: string, name: string | undefined, options: WorkflowOptions) {
  if (!name) {
    console.log(chalk.red('请指定工作流名称'));
    console.log(chalk.yellow('可用工作流: qa workflow list'));
    return;
  }
  
  if (!await fs.pathExists(configPath)) {
    console.log(chalk.red('配置文件不存在'));
    return;
  }
  
  const config = await fs.readJson(configPath);
  const coordination = config.coordination || {};
  
  if (!coordination.enabled) {
    console.log(chalk.yellow('多代理协调未启用'));
    console.log(chalk.dim('请先运行 /enable-coordination 启用'));
    return;
  }
  
  const workflow = coordination.workflows?.[name];
  if (!workflow) {
    console.log(chalk.red('工作流不存在: ' + name));
    return;
  }
  
  const spinner = ora('启动工作流 ' + name + '...').start();
  
  if (options.dryRun) {
    spinner.info(chalk.yellow('模拟模式 - 不实际执行'));
    console.log('\n' + chalk.bold('工作流配置:'));
    console.log(JSON.stringify(workflow, null, 2));
    return;
  }
  
  // 实际执行需要与 OpenCode 集成
  spinner.warn(chalk.yellow('工作流执行需要 OpenCode 环境'));
  console.log('\n' + chalk.dim('请在 OpenCode 中运行: /run-workflow ' + name));
}

async function workflowStatus(configPath: string, name: string | undefined) {
  if (!await fs.pathExists(configPath)) {
    console.log(chalk.yellow('配置文件不存在'));
    return;
  }
  
  const config = await fs.readJson(configPath);
  const coordination = config.coordination || {};
  
  console.log(chalk.bold('\n协调状态:\n'));
  console.log('  启用状态: ' + (coordination.enabled ? chalk.green('已启用') : chalk.gray('未启用')));
  
  if (coordination.settings) {
    console.log('  最大并行代理: ' + chalk.cyan(coordination.settings.maxParallelAgents || 3));
    console.log('  默认超时: ' + chalk.cyan((coordination.settings.defaultTimeout || 300000) / 1000 + 's'));
  }
  
  if (name) {
    const workflow = coordination.workflows?.[name];
    if (workflow) {
      console.log('\n' + chalk.bold('工作流: ' + name));
      console.log(JSON.stringify(workflow, null, 2));
    } else {
      console.log(chalk.yellow('工作流不存在: ' + name));
    }
  }
}
