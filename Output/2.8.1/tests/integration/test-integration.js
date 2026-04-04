#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

class QuickAgentsIntegrationTester {
  constructor() {
    this.results = {
      total: 0,
      passed: 0,
      failed: 0,
      errors: []
    };
    this.agents = {};
    this.skills = {};
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

  loadAgents() {
    const agentsDir = '.opencode/agents';
    const files = fs.readdirSync(agentsDir).filter(f => f.endsWith('.md') && f !== 'README.md');
    
    files.forEach(file => {
      const content = fs.readFileSync(path.join(agentsDir, file), 'utf-8');
      const agentName = file.replace('.md', '');
      
      // 提取YAML配置
      const yamlMatch = content.match(/---\n([\s\S]*?)\n---/);
      if (yamlMatch) {
        const yaml = yamlMatch[1];
        this.agents[agentName] = {
          file,
          yaml,
          content
        };
      }
    });
  }

  loadSkills() {
    const skillsDir = '.opencode/skills';
    const dirs = fs.readdirSync(skillsDir, { withFileTypes: true })
      .filter(d => d.isDirectory())
      .map(d => d.name);
    
    dirs.forEach(skillName => {
      const skillMdPath = path.join(skillsDir, skillName, 'SKILL.md');
      if (fs.existsSync(skillMdPath)) {
        const content = fs.readFileSync(skillMdPath, 'utf-8');
        this.skills[skillName] = {
          path: path.join(skillsDir, skillName),
          content
        };
      }
    });
  }

  testOrchestratorIntegration() {
    this.log('=== 测试Orchestrator集成 ===', 'info');
    
    // 测试1: orchestrator代理存在
    const hasOrchestrator = this.agents['orchestrator'] !== undefined;
    this.test('orchestrator代理存在', hasOrchestrator);
    
    if (hasOrchestrator) {
      const orchestrator = this.agents['orchestrator'].content;
      
      // 测试2: orchestrator能协调其他代理
      const canCoordinate = orchestrator.includes('@') || orchestrator.includes('代理') || orchestrator.includes('agent');
      this.test('orchestrator具有协调能力', canCoordinate);
      
      // 测试3: orchestrator有任务分解能力
      const canDecompose = orchestrator.includes('分解') || orchestrator.includes('任务') || orchestrator.includes('subtask');
      this.test('orchestrator具有任务分解能力', canDecompose);
    }
  }

  testBackgroundAgentsIntegration() {
    this.log('=== 测试Background Agents集成 ===', 'info');
    
    // 测试1: background-agents-skill存在
    const hasBackgroundSkill = this.skills['background-agents-skill'] !== undefined;
    this.test('background-agents-skill存在', hasBackgroundSkill);
    
    if (hasBackgroundSkill) {
      const skill = this.skills['background-agents-skill'].content;
      
      // 测试2: 有并发控制
      const hasConcurrency = skill.includes('并发') || skill.includes('concurrent') || skill.includes('parallel');
      this.test('background-agents具有并发控制', hasConcurrency);
      
      // 测试3: 有任务队列
      const hasQueue = skill.includes('队列') || skill.includes('queue') || skill.includes('任务');
      this.test('background-agents具有任务队列', hasQueue);
    }
  }

  testBoulderIntegration() {
    this.log('=== 测试Boulder进度追踪集成 ===', 'info');
    
    // 测试1: boulder-tracking-skill存在
    const hasBoulderSkill = this.skills['boulder-tracking-skill'] !== undefined;
    this.test('boulder-tracking-skill存在', hasBoulderSkill);
    
    // 测试2: start-work命令存在
    const commandsDir = '.opencode/commands';
    const hasStartWork = fs.existsSync(path.join(commandsDir, 'start-work.md'));
    this.test('start-work命令存在', hasStartWork);
    
    // 测试3: boulder.json配置目录存在
    const hasBoulderDir = fs.existsSync('.quickagents');
    this.test('.quickagents目录存在', hasBoulderDir);
    
    if (hasBoulderSkill) {
      const skill = this.skills['boulder-tracking-skill'].content;
      
      // 测试4: 有跨会话恢复能力
      const hasRecovery = skill.includes('恢复') || skill.includes('resume') || skill.includes('会话');
      this.test('boulder具有跨会话恢复能力', hasRecovery);
    }
  }

  testCategoryIntegration() {
    this.log('=== 测试Category系统集成 ===', 'info');
    
    // 测试1: category-system-skill存在
    const hasCategorySkill = this.skills['category-system-skill'] !== undefined;
    this.test('category-system-skill存在', hasCategorySkill);
    
    // 测试2: categories.json配置存在
    const hasCategoriesConfig = fs.existsSync('.opencode/config/categories.json');
    this.test('categories.json配置存在', hasCategoriesConfig);
    
    if (hasCategoriesConfig) {
      try {
        const config = JSON.parse(fs.readFileSync('.opencode/config/categories.json', 'utf-8'));
        
        // 测试3: 有多个category定义
        const hasMultipleCategories = config.categories && Object.keys(config.categories).length >= 3;
        this.test('categories.json有多个Category', hasMultipleCategories, `(${Object.keys(config.categories || {}).length}个)`);
        
        // 测试4: 每个category有fallback
        const hasFallbacks = Object.values(config.categories || {}).every(c => c.fallback && c.fallback.length > 0);
        this.test('所有Category有fallback机制', hasFallbacks);
        
      } catch (error) {
        this.test('categories.json格式有效', false, error.message);
      }
    }
  }

  testMultiModelIntegration() {
    this.log('=== 测试多模型协同集成 ===', 'info');
    
    // 测试1: multi-model-skill存在
    const hasMultiModelSkill = this.skills['multi-model-skill'] !== undefined;
    this.test('multi-model-skill存在', hasMultiModelSkill);
    
    // 测试2: models.json配置存在
    const hasModelsConfig = fs.existsSync('.opencode/config/models.json');
    this.test('models.json配置存在', hasModelsConfig);
    
    if (hasModelsConfig) {
      try {
        const config = JSON.parse(fs.readFileSync('.opencode/config/models.json', 'utf-8'));
        
        // 测试3: 有多个模型定义
        const hasMultipleModels = config.models && Object.keys(config.models).length >= 3;
        this.test('models.json有多个模型', hasMultipleModels, `(${Object.keys(config.models || {}).length}个)`);
        
        // 测试4: 有路由配置
        const hasRouting = config.routing !== undefined;
        this.test('models.json有路由配置', hasRouting);
        
      } catch (error) {
        this.test('models.json格式有效', false, error.message);
      }
    }
  }

  testPrometheusIntegration() {
    this.log('=== 测试Prometheus规划系统集成 ===', 'info');
    
    // 测试1: prometheus代理存在
    const hasPrometheus = this.agents['prometheus'] !== undefined;
    this.test('prometheus代理存在', hasPrometheus);
    
    // 测试2: metis代理存在
    const hasMetis = this.agents['metis'] !== undefined;
    this.test('metis代理存在', hasMetis);
    
    // 测试3: momus代理存在
    const hasMomus = this.agents['momus'] !== undefined;
    this.test('momus代理存在', hasMomus);
    
    // 测试4: 三方协作
    if (hasPrometheus && hasMetis && hasMomus) {
      const prometheus = this.agents['prometheus'].content;
      const metis = this.agents['metis'].content;
      const momus = this.agents['momus'].content;
      
      const hasCollaboration = 
        (prometheus.includes('metis') || prometheus.includes('Metis')) &&
        (prometheus.includes('momus') || prometheus.includes('Momus'));
      this.test('Prometheus/Metis/Momus三方协作', hasCollaboration);
    }
  }

  testLSPASTIntegration() {
    this.log('=== 测试LSP/AST集成 ===', 'info');
    
    // 测试1: lsp-ast-skill存在
    const hasLSPSkill = this.skills['lsp-ast-skill'] !== undefined;
    this.test('lsp-ast-skill存在', hasLSPSkill);
    
    // 测试2: lsp-config.json配置存在
    const hasLSPConfig = fs.existsSync('.opencode/config/lsp-config.json');
    this.test('lsp-config.json配置存在', hasLSPConfig);
    
    if (hasLSPConfig) {
      try {
        const config = JSON.parse(fs.readFileSync('.opencode/config/lsp-config.json', 'utf-8'));
        
        // 测试3: 有多个LSP配置
        const hasMultipleLSPs = config.languages && Object.keys(config.languages).length >= 3;
        this.test('lsp-config.json有多个LSP配置', hasMultipleLSPs, `(${Object.keys(config.languages || {}).length}个)`);
        
      } catch (error) {
        this.test('lsp-config.json格式有效', false, error.message);
      }
    }
  }

  testTodoEnforcerIntegration() {
    this.log('=== 测试Todo Enforcer集成 ===', 'info');
    
    // 测试1: todo-continuation-enforcer存在
    const hooksDir = '.opencode/hooks';
    const hasEnforcer = fs.existsSync(path.join(hooksDir, 'todo-continuation-enforcer.md'));
    this.test('todo-continuation-enforcer存在', hasEnforcer);
    
    if (hasEnforcer) {
      const content = fs.readFileSync(path.join(hooksDir, 'todo-continuation-enforcer.md'), 'utf-8');
      
      // 测试2: 有idle检测
      const hasIdleDetection = content.includes('idle') || content.includes('空闲') || content.includes('停止');
      this.test('Todo Enforcer有idle检测', hasIdleDetection);
      
      // 测试3: 有强制继续逻辑
      const hasEnforceLogic = content.includes('强制') || content.includes('enforce') || content.includes('继续');
      this.test('Todo Enforcer有强制继续逻辑', hasEnforceLogic);
    }
  }

  run() {
    this.log('开始集成测试...', 'info');
    console.log('');
    
    // 加载配置
    this.loadAgents();
    this.loadSkills();
    
    // 执行测试
    this.testOrchestratorIntegration();
    console.log('');
    
    this.testBackgroundAgentsIntegration();
    console.log('');
    
    this.testBoulderIntegration();
    console.log('');
    
    this.testCategoryIntegration();
    console.log('');
    
    this.testMultiModelIntegration();
    console.log('');
    
    this.testPrometheusIntegration();
    console.log('');
    
    this.testLSPASTIntegration();
    console.log('');
    
    this.testTodoEnforcerIntegration();
    console.log('');
    
    // 生成报告
    this.log('=== 集成测试报告 ===', 'info');
    console.log(`总计: ${this.results.total}`);
    console.log(`通过: ${this.results.passed} ✅`);
    console.log(`失败: ${this.results.failed} ❌`);
    console.log(`成功率: ${((this.results.passed / this.results.total) * 100).toFixed(1)}%`);
    
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
const tester = new QuickAgentsIntegrationTester();
const results = tester.run();

// 返回退出码
process.exit(results.failed > 0 ? 1 : 0);
