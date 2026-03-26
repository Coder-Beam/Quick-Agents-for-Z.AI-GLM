import { Command } from 'commander';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { initCommand } from './commands/init.js';
import { startCommand } from './commands/start.js';
import { statusCommand } from './commands/status.js';
import { agentCommand } from './commands/agent.js';
import { skillCommand } from './commands/skill.js';
import { workflowCommand } from './commands/workflow.js';
import { configCommand } from './commands/config.js';
import { metricsCommand } from './commands/metrics.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const pkg = JSON.parse(
  readFileSync(join(__dirname, '../package.json'), 'utf-8')
);

const program = new Command();

program
  .name('quickagents')
  .alias('qa')
  .description('QuickAgents CLI - AI代理项目初始化系统')
  .version(pkg.version)
  .option('-v, --verbose', '显示详细输出')
  .option('--no-color', '禁用彩色输出');

program
  .command('init')
  .description('在当前目录初始化 QuickAgents 项目')
  .option('-t, --template <name>', '使用指定模板', 'default')
  .option('-f, --force', '强制覆盖现有文件')
  .option('--skip-skills', '跳过技能安装')
  .action(initCommand);

program
  .command('start')
  .description('启动 QuickAgents 会话')
  .option('-a, --agent <name>', '指定初始代理')
  .option('-t, --task <id>', '恢复指定任务')
  .action(startCommand);

program
  .command('status')
  .description('显示项目状态')
  .option('-j, --json', 'JSON 格式输出')
  .option('-d, --detailed', '显示详细信息')
  .action(statusCommand);

program
  .command('agent')
  .description('管理代理')
  .argument('<action>', 'list | show | enable | disable')
  .argument('[name]', '代理名称')
  .option('-c, --category <cat>', '按类别筛选')
  .action(agentCommand);

program
  .command('skill')
  .description('管理技能')
  .argument('<action>', 'list | install | remove | update')
  .argument('[name]', '技能名称')
  .option('-r, --registry <url>', '指定技能仓库')
  .action(skillCommand);

program
  .command('workflow')
  .description('管理工作流')
  .argument('<action>', 'list | run | status')
  .argument('[name]', '工作流名称')
  .option('-t, --timeout <ms>', '超时时间')
  .option('--dry-run', '模拟执行')
  .action(workflowCommand);

program
  .command('config')
  .description('管理配置')
  .argument('<action>', 'get | set | list | reset')
  .argument('[key]', '配置键')
  .argument('[value]', '配置值')
  .action(configCommand);

program
  .command('metrics')
  .description('查看项目指标')
  .option('-p, --period <days>', '统计周期（天）', '7')
  .option('-f, --format <type>', '输出格式', 'table')
  .action(metricsCommand);

program.parse();
