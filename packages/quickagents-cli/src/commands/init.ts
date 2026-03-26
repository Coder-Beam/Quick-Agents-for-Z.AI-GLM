import fs from 'fs-extra';
import path from 'path';
import chalk from 'chalk';
import ora from 'ora';
import Enquirer from 'enquirer';
import type { Command } from 'commander';

const prompt = Enquirer.prompt;

interface InitOptions {
  template: string;
  force: boolean;
  skipSkills: boolean;
}

const TEMPLATES = {
  default: {
    name: 'Default',
    description: '标准 QuickAgents 项目配置',
    agents: ['yinglong-init', 'boyi-consult', 'chisongzi-advise', 'cangjie-doc'],
    skills: ['project-memory-skill', 'inquiry-skill', 'tdd-workflow-skill']
  },
  minimal: {
    name: 'Minimal',
    description: '最小化配置，仅包含核心代理',
    agents: ['yinglong-init'],
    skills: ['project-memory-skill']
  },
  full: {
    name: 'Full',
    description: '完整配置，包含所有代理和技能',
    agents: 'all',
    skills: 'all'
  }
};

export async function initCommand(options: InitOptions, command: Command) {
  const spinner = ora('初始化 QuickAgents 项目...').start();
  
  try {
    const cwd = process.cwd();
    
    // 检查是否已初始化
    const opencodeDir = path.join(cwd, '.opencode');
    if (await fs.pathExists(opencodeDir) && !options.force) {
      spinner.warn('项目已初始化');
      const result = await prompt<{ proceed: boolean }>({
        type: 'confirm',
        name: 'proceed',
        message: '是否覆盖现有配置？',
        initial: false
      });
      
      if (!result.proceed) {
        console.log(chalk.yellow('初始化已取消'));
        return;
      }
    }
    
    // 选择模板
    let template = options.template;
    if (template === 'default' && !options.force) {
      const result = await prompt<{ selectedTemplate: string }>({
        type: 'select',
        name: 'selectedTemplate',
        message: '选择项目模板:',
        choices: Object.entries(TEMPLATES).map(([key, value]) => ({
          name: key,
          message: `${value.name} - ${value.description}`
        }))
      });
      template = result.selectedTemplate;
    }
    
    spinner.text = '创建目录结构...';
    
    // 创建目录结构
    await fs.ensureDir(opencodeDir);
    await fs.ensureDir(path.join(opencodeDir, 'agents'));
    await fs.ensureDir(path.join(opencodeDir, 'skills'));
    await fs.ensureDir(path.join(opencodeDir, 'commands'));
    await fs.ensureDir(path.join(opencodeDir, 'config'));
    await fs.ensureDir(path.join(opencodeDir, 'hooks'));
    await fs.ensureDir(path.join(opencodeDir, 'memory'));
    await fs.ensureDir(path.join(cwd, 'Docs'));
    
    spinner.text = '生成配置文件...';
    
    // 生成配置文件
    await generateConfig(opencodeDir, template);
    
    spinner.text = '创建文档结构...';
    
    // 创建文档文件
    await createDocs(cwd);
    
    if (!options.skipSkills) {
      spinner.text = '安装默认技能...';
      await installDefaultSkills(opencodeDir, template);
    }
    
    spinner.succeed(chalk.green('QuickAgents 项目初始化完成！'));
    
    console.log('\n' + chalk.bold('下一步:'));
    console.log('  1. 查看 ' + chalk.cyan('Docs/MEMORY.md') + ' 了解项目记忆系统');
    console.log('  2. 运行 ' + chalk.cyan('qa start') + ' 启动会话');
    console.log('  3. 或直接发送 ' + chalk.cyan('"启动QuickAgent"') + ' 开始');
    
  } catch (error) {
    spinner.fail(chalk.red('初始化失败'));
    console.error(error);
    process.exit(1);
  }
}

async function generateConfig(opencodeDir: string, template: string) {
  const templateConfig = TEMPLATES[template as keyof typeof TEMPLATES] || TEMPLATES.default;
  
  // 生成 opencode.json
  const opencodeConfig = {
    version: '1.0.0',
    project: {
      name: path.basename(process.cwd()),
      type: 'auto-detect'
    },
    agents: {
      autoLoad: templateConfig.agents === 'all',
      default: templateConfig.agents === 'all' ? [] : templateConfig.agents
    },
    skills: {
      autoLoad: templateConfig.skills === 'all',
      default: templateConfig.skills === 'all' ? [] : templateConfig.skills
    }
  };
  
  await fs.writeJson(path.join(opencodeDir, 'opencode.json'), opencodeConfig, { spaces: 2 });
  
  // 生成 models.json
  const modelsConfig = {
    default: 'zhipuai-coding-plan/glm-5',
    models: {
      'zhipuai-coding-plan/glm-5': {
        provider: 'zhipu',
        model: 'glm-5',
        contextWindow: 128000
      }
    }
  };
  
  await fs.writeJson(path.join(opencodeDir, 'config', 'models.json'), modelsConfig, { spaces: 2 });
}

async function createDocs(cwd: string) {
  const docsDir = path.join(cwd, 'Docs');
  
  // 创建 MEMORY.md
  const memoryContent = `---
memory_type: project
created_at: ${new Date().toISOString()}
version: 1.0.0
---

# 项目记忆文件

> 基于《Memory in the Age of AI Agents》论文设计的三维记忆系统

## 一、Factual Memory（事实记忆）

### 1.1 项目元信息

| 属性 | 值 |
|------|-----|
| 项目名称 | ${path.basename(cwd)} |
| 项目路径 | ${cwd} |
| 技术栈 | 待确认 |
| 启动时间 | ${new Date().toLocaleDateString('zh-CN')} |

## 二、Experiential Memory（经验记忆）

### 2.1 操作历史

| 时间 | 操作 | 结果 | 备注 |
|------|------|------|------|
| ${new Date().toLocaleDateString('zh-CN')} | 项目初始化 | 成功 | 使用 quickagents-cli |

## 三、Working Memory（工作记忆）

### 3.1 当前状态

| 属性 | 值 |
|------|-----|
| 当前任务 | 无 |
| 进度 | 0% |
| 当前阶段 | 初始化完成 |
`;
  
  await fs.writeFile(path.join(docsDir, 'MEMORY.md'), memoryContent);
  
  // 创建 TASKS.md
  const tasksContent = `# 任务管理

## 当前迭代

| 任务ID | 任务名称 | 优先级 | 状态 | 负责人 | 开始时间 | 完成时间 |
|--------|----------|--------|------|--------|----------|----------|
| T001 | 项目需求确认 | P0 | 待开始 | - | - | - |

## 待办任务

### P0 - 紧急

- [ ] 确认项目需求
- [ ] 确认技术栈

---

*最后更新: ${new Date().toLocaleDateString('zh-CN')}*
`;
  
  await fs.writeFile(path.join(docsDir, 'TASKS.md'), tasksContent);
}

async function installDefaultSkills(opencodeDir: string, template: string) {
  // 这里可以添加从远程仓库下载技能的逻辑
  // 目前仅创建占位目录
  const skillsDir = path.join(opencodeDir, 'skills');
  
  const templateConfig = TEMPLATES[template as keyof typeof TEMPLATES] || TEMPLATES.default;
  const skills = templateConfig.skills === 'all' 
    ? ['project-memory-skill', 'inquiry-skill', 'tdd-workflow-skill', 'git-commit-skill', 'code-review-skill']
    : templateConfig.skills as string[];
  
  for (const skill of skills) {
    await fs.ensureDir(path.join(skillsDir, skill));
  }
}
