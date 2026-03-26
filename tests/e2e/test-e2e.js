#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

class QuickAgentsE2ETester {
  constructor() {
    this.results = {
      total: 0,
      passed: 0,
      failed: 0,
      errors: [],
      scenarios: []
    };
  }

  log(message, type = 'info') {
    const timestamp = new Date().toISOString();
    const prefix = type === 'error' ? '❌' : type === 'success' ? '✅' : 'ℹ️';
    console.log(`${prefix} [${timestamp}] ${message}`);
  }

  test(name, condition, details = '') {
    this.results.total++;
    if (condition) {
      this.results.passed++;
      this.log(`${name} - PASSED ${details}`, 'success');
      return true;
    } else {
      this.results.failed++;
      this.results.errors.push({ name, details });
      this.log(`${name} - FAILED ${details}`, 'error');
      return false;
    }
  }

  scenario(name, description) {
    this.log(`\n场景: ${name}`, 'info');
    this.log(`描述: ${description}`, 'info');
    console.log('---');
  }

  testScenario1_NewProjectInitialization() {
    this.scenario('场景1', '新项目初始化流程');
    
    // 模拟：用户发送"启动QuickAgent"
    this.log('步骤1: 用户发送"启动QuickAgent"', 'info');
    
    // 验证1: project-initializer代理存在
    const hasInitializer = fs.existsSync('.opencode/agents/project-initializer.md');
    this.test('project-initializer代理存在', hasInitializer);
    
    // 验证2: project-detector-skill存在
    const hasDetector = fs.existsSync('.opencode/skills/project-detector-skill/SKILL.md');
    this.test('project-detector-skill存在', hasDetector);
    
    // 模拟：系统检测项目类型
    this.log('步骤2: 系统检测项目类型', 'info');
    
    // 验证3: 检测逻辑存在
    if (hasDetector) {
      const detectorContent = fs.readFileSync('.opencode/skills/project-detector-skill/SKILL.md', 'utf-8');
      const hasDetection = detectorContent.includes('检测') || detectorContent.includes('detect');
      this.test('项目检测逻辑存在', hasDetection);
    }
    
    // 模拟：开始12轮需求澄清
    this.log('步骤3: 开始12轮需求澄清', 'info');
    
    // 验证4: inquiry-card-skill存在
    const hasInquiry = fs.existsSync('.opencode/skills/inquiry-card-skill/SKILL.md');
    this.test('inquiry-card-skill存在', hasInquiry);
    
    // 验证5: 有12轮设计
    if (hasInquiry) {
      const inquiryContent = fs.readFileSync('.opencode/skills/inquiry-card-skill/SKILL.md', 'utf-8');
      const has12Rounds = inquiryContent.includes('12') || inquiryContent.includes('十二');
      this.test('12轮需求澄清设计存在', has12Rounds);
    }
    
    // 模拟：创建项目文档
    this.log('步骤4: 创建项目文档', 'info');
    
    // 验证6: 文档模板存在
    const hasMemoryTemplate = fs.existsSync('Docs/MEMORY.md');
    const hasTasksTemplate = fs.existsSync('Docs/TASKS.md');
    this.test('MEMORY.md模板存在', hasMemoryTemplate);
    this.test('TASKS.md模板存在', hasTasksTemplate);
    
    this.results.scenarios.push({
      name: '新项目初始化',
      passed: this.results.passed,
      total: this.results.total
    });
  }

  testScenario2_ExistingProjectAnalysis() {
    const initialTotal = this.results.total;
    const initialPassed = this.results.passed;
    
    this.scenario('场景2', '现有项目分析流程');
    
    // 模拟：系统检测到现有项目
    this.log('步骤1: 系统检测到现有项目', 'info');
    
    // 验证1: package.json检测逻辑
    const hasPackageDetection = fs.existsSync('package.json');
    this.test('能检测package.json', hasPackageDetection);
    
    // 模拟：询问用户意图
    this.log('步骤2: 询问用户意图（继续开发/重新开始）', 'info');
    
    // 验证2: project-initializer有询问逻辑
    if (fs.existsSync('.opencode/agents/project-initializer.md')) {
      const content = fs.readFileSync('.opencode/agents/project-initializer.md', 'utf-8');
      const hasIntentQuestion = content.includes('继续') || content.includes('重新') || content.includes('意图');
      this.test('有用户意图询问逻辑', hasIntentQuestion);
    }
    
    // 模拟：加载现有配置
    this.log('步骤3: 加载现有配置和文档', 'info');
    
    // 验证3: 能读取MEMORY.md
    const canReadMemory = fs.existsSync('Docs/MEMORY.md');
    this.test('能读取MEMORY.md', canReadMemory);
    
    // 验证4: 能读取boulder.json
    const canReadBoulder = fs.existsSync('.quickagents/boulder.json');
    this.test('能读取boulder.json', canReadBoulder);
    
    this.results.scenarios.push({
      name: '现有项目分析',
      passed: this.results.passed - initialPassed,
      total: this.results.total - initialTotal
    });
  }

  testScenario3_CrossSessionRecovery() {
    const initialTotal = this.results.total;
    const initialPassed = this.results.passed;
    
    this.scenario('场景3', '跨会话工作恢复流程');
    
    // 模拟：会话结束，保存进度
    this.log('步骤1: 会话结束，保存进度', 'info');
    
    // 验证1: boulder.json存在
    const hasBoulder = fs.existsSync('.quickagents/boulder.json');
    this.test('boulder.json存在', hasBoulder);
    
    // 验证2: boulder格式正确
    if (hasBoulder) {
      try {
        const boulder = JSON.parse(fs.readFileSync('.quickagents/boulder.json', 'utf-8'));
        const hasValidFormat = boulder.session_id && boulder.total_tasks !== undefined;
        this.test('boulder.json格式正确', hasValidFormat);
      } catch (error) {
        this.test('boulder.json格式正确', false, error.message);
      }
    }
    
    // 模拟：新会话开始
    this.log('步骤2: 新会话开始，发送/start-work', 'info');
    
    // 验证3: start-work命令存在
    const hasStartWork = fs.existsSync('.opencode/commands/start-work.md');
    this.test('start-work命令存在', hasStartWork);
    
    // 验证4: start-work有恢复逻辑
    if (hasStartWork) {
      const content = fs.readFileSync('.opencode/commands/start-work.md', 'utf-8');
      const hasRecoveryLogic = content.includes('恢复') || content.includes('resume') || content.includes('boulder');
      this.test('start-work有恢复逻辑', hasRecoveryLogic);
    }
    
    // 模拟：恢复工作状态
    this.log('步骤3: 恢复工作状态', 'info');
    
    // 验证5: 有notepad系统
    if (hasBoulder) {
      const boulder = JSON.parse(fs.readFileSync('.quickagents/boulder.json', 'utf-8'));
      const hasNotepad = boulder.notepad !== undefined;
      this.test('有notepad系统', hasNotepad);
    }
    
    this.results.scenarios.push({
      name: '跨会话恢复',
      passed: this.results.passed - initialPassed,
      total: this.results.total - initialTotal
    });
  }

  testScenario4_ComplexTaskExecution() {
    const initialTotal = this.results.total;
    const initialPassed = this.results.passed;
    
    this.scenario('场景4', '复杂任务执行流程');
    
    // 模拟：用户发送ultrawork命令
    this.log('步骤1: 用户发送/ultrawork命令', 'info');
    
    // 验证1: ultrawork命令存在
    const hasUltrawork = fs.existsSync('.opencode/commands/ultrawork.md');
    this.test('ultrawork命令存在', hasUltrawork);
    
    // 模拟：orchestrator分解任务
    this.log('步骤2: orchestrator分解任务', 'info');
    
    // 验证2: orchestrator存在
    const hasOrchestrator = fs.existsSync('.opencode/agents/orchestrator.md');
    this.test('orchestrator代理存在', hasOrchestrator);
    
    // 验证3: 有任务分解逻辑
    if (hasOrchestrator) {
      const content = fs.readFileSync('.opencode/agents/orchestrator.md', 'utf-8');
      const hasDecomposition = content.includes('分解') || content.includes('任务') || content.includes('subtask');
      this.test('orchestrator有任务分解逻辑', hasDecomposition);
    }
    
    // 模拟：并行执行子任务
    this.log('步骤3: 并行执行子任务', 'info');
    
    // 验证4: background-agents-skill存在
    const hasBackground = fs.existsSync('.opencode/skills/background-agents-skill/SKILL.md');
    this.test('background-agents-skill存在', hasBackground);
    
    // 模拟：汇总结果
    this.log('步骤4: 汇总结果并报告', 'info');
    
    // 验证5: 有结果汇总逻辑
    if (hasOrchestrator) {
      const content = fs.readFileSync('.opencode/agents/orchestrator.md', 'utf-8');
      const hasAggregation = content.includes('汇总') || content.includes('报告') || content.includes('result');
      this.test('orchestrator有结果汇总逻辑', hasAggregation);
    }
    
    this.results.scenarios.push({
      name: '复杂任务执行',
      passed: this.results.passed - initialPassed,
      total: this.results.total - initialTotal
    });
  }

  testScenario5_MultiModelCollaboration() {
    const initialTotal = this.results.total;
    const initialPassed = this.results.passed;
    
    this.scenario('场景5', '多模型协同流程');
    
    // 模拟：系统检测任务类型
    this.log('步骤1: 系统检测任务类型', 'info');
    
    // 验证1: category-system-skill存在
    const hasCategory = fs.existsSync('.opencode/skills/category-system-skill/SKILL.md');
    this.test('category-system-skill存在', hasCategory);
    
    // 验证2: categories.json存在
    const hasCategoriesConfig = fs.existsSync('.opencode/config/categories.json');
    this.test('categories.json存在', hasCategoriesConfig);
    
    // 模拟：选择合适的模型
    this.log('步骤2: 选择合适的模型', 'info');
    
    // 验证3: models.json存在
    const hasModelsConfig = fs.existsSync('.opencode/config/models.json');
    this.test('models.json存在', hasModelsConfig);
    
    // 验证4: 有fallback机制
    if (hasCategoriesConfig) {
      try {
        const config = JSON.parse(fs.readFileSync('.opencode/config/categories.json', 'utf-8'));
        const hasFallbacks = Object.values(config.categories || {}).some(c => c.fallback && c.fallback.length > 0);
        this.test('有fallback机制', hasFallbacks);
      } catch (error) {
        this.test('有fallback机制', false, error.message);
      }
    }
    
    // 模拟：执行任务
    this.log('步骤3: 使用选定模型执行任务', 'info');
    
    // 验证5: multi-model-skill存在
    const hasMultiModel = fs.existsSync('.opencode/skills/multi-model-skill/SKILL.md');
    this.test('multi-model-skill存在', hasMultiModel);
    
    this.results.scenarios.push({
      name: '多模型协同',
      passed: this.results.passed - initialPassed,
      total: this.results.total - initialTotal
    });
  }

  run() {
    this.log('开始E2E测试...', 'info');
    console.log('');
    
    // 执行所有场景测试
    this.testScenario1_NewProjectInitialization();
    console.log('');
    
    this.testScenario2_ExistingProjectAnalysis();
    console.log('');
    
    this.testScenario3_CrossSessionRecovery();
    console.log('');
    
    this.testScenario4_ComplexTaskExecution();
    console.log('');
    
    this.testScenario5_MultiModelCollaboration();
    console.log('');
    
    // 生成报告
    this.log('=== E2E测试报告 ===', 'info');
    console.log(`总计: ${this.results.total}`);
    console.log(`通过: ${this.results.passed} ✅`);
    console.log(`失败: ${this.results.failed} ❌`);
    console.log(`成功率: ${((this.results.passed / this.results.total) * 100).toFixed(1)}%`);
    
    console.log('\n场景覆盖:');
    this.results.scenarios.forEach(s => {
      console.log(`- ${s.name}: ${s.passed}/${s.total} 通过`);
    });
    
    if (this.results.failed > 0) {
      console.log('\n失败项:');
      this.results.errors.forEach((err, i) => {
        console.log(`${i + 1}. ${err.name} - ${err.details}`);
      });
    }
    
    return this.results;
  }
}

// 运行测试
const tester = new QuickAgentsE2ETester();
const results = tester.run();

// 返回退出码
process.exit(results.failed > 0 ? 1 : 0);
