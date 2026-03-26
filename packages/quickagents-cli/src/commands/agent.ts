import fs from 'fs-extra';
import path from 'path';
import chalk from 'chalk';
import type { Command } from 'commander';

interface AgentOptions {
  category?: string;
}

export async function agentCommand(action: string, name: string | undefined, options: AgentOptions, command: Command) {
  const cwd = process.cwd();
  const opencodeDir = path.join(cwd, '.opencode');
  const agentsDir = path.join(opencodeDir, 'agents');
  
  switch (action) {
    case 'list':
      await listAgents(agentsDir, options.category);
      break;
    case 'show':
      await showAgent(agentsDir, name);
      break;
    case 'enable':
      await toggleAgent(agentsDir, name, true);
      break;
    case 'disable':
      await toggleAgent(agentsDir, name, false);
      break;
    default:
      console.log(chalk.red('未知操作: ' + action));
      console.log(chalk.yellow('可用操作: list, show, enable, disable'));
  }
}

async function listAgents(agentsDir: string, category?: string) {
  if (!await fs.pathExists(agentsDir)) {
    console.log(chalk.yellow('代理目录不存在'));
    return;
  }
  
  const files = await fs.readdir(agentsDir);
  const agents = files.filter(f => f.endsWith('.md'));
  
  if (agents.length === 0) {
    console.log(chalk.yellow('没有找到代理'));
    return;
  }
  
  console.log(chalk.bold('\n可用代理 (' + agents.length + '):\n'));
  
  for (const agent of agents) {
    const agentPath = path.join(agentsDir, agent);
    const content = await fs.readFile(agentPath, 'utf-8');
    
    // 解析 front matter
    const frontMatter = parseFrontMatter(content);
    const agentName = agent.replace('.md', '');
    
    console.log('  ' + chalk.cyan(agentName));
    if (frontMatter.description) {
      console.log('    ' + chalk.dim(frontMatter.description));
    }
  }
}

async function showAgent(agentsDir: string, name: string | undefined) {
  if (!name) {
    console.log(chalk.red('请指定代理名称'));
    return;
  }
  
  const agentPath = path.join(agentsDir, name + '.md');
  
  if (!await fs.pathExists(agentPath)) {
    console.log(chalk.red('代理不存在: ' + name));
    return;
  }
  
  const content = await fs.readFile(agentPath, 'utf-8');
  const frontMatter = parseFrontMatter(content);
  
  console.log(chalk.bold('\n代理信息:\n'));
  console.log('  名称: ' + chalk.cyan(name));
  console.log('  描述: ' + (frontMatter.description || chalk.dim('无')));
  console.log('  模式: ' + (frontMatter.mode || chalk.dim('默认')));
  console.log('  模型: ' + (frontMatter.model || chalk.dim('继承')));
  
  if (frontMatter.tools) {
    console.log('  工具权限:');
    for (const [tool, permission] of Object.entries(frontMatter.tools)) {
      const color = permission ? chalk.green : chalk.red;
      console.log('    - ' + tool + ': ' + color(String(permission)));
    }
  }
}

async function toggleAgent(agentsDir: string, name: string | undefined, enable: boolean) {
  if (!name) {
    console.log(chalk.red('请指定代理名称'));
    return;
  }
  
  const agentPath = path.join(agentsDir, name + '.md');
  
  if (!await fs.pathExists(agentPath)) {
    console.log(chalk.red('代理不存在: ' + name));
    return;
  }
  
  // 这里可以添加实际的启用/禁用逻辑
  // 目前仅输出信息
  const action = enable ? '启用' : '禁用';
  console.log(chalk.green('✓') + ' 代理 ' + chalk.cyan(name) + ' 已' + action);
}

function parseFrontMatter(content: string): Record<string, unknown> {
  const match = content.match(/^---\n([\s\S]*?)\n---/);
  if (!match) return {};
  
  const frontMatter: Record<string, unknown> = {};
  const lines = match[1].split('\n');
  
  for (const line of lines) {
    const [key, ...valueParts] = line.split(':');
    if (key && valueParts.length > 0) {
      const rawValue = valueParts.join(':').trim();
      let value: unknown = rawValue;
      
      // 解析布尔值
      if (rawValue === 'true') value = true;
      else if (rawValue === 'false') value = false;
      // 解析对象（简化处理）
      else if (rawValue.startsWith('{')) {
        try {
          value = JSON.parse(rawValue);
        } catch {
          // 保持原值
        }
      }
      
      frontMatter[key.trim()] = value;
    }
  }
  
  return frontMatter;
}
