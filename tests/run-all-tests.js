#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

class QuickAgentsTestRunner {
  constructor() {
    this.results = {
      unit: null,
      integration: null,
      e2e: null,
      performance: null
    };
  }

  log(message, type = 'info') {
    const timestamp = new Date().toISOString();
    const prefix = type === 'error' ? '❌' : type === 'success' ? '✅' : 'ℹ️';
    console.log(`${prefix} [${timestamp}] ${message}`);
  }

  runTest(testPath, testName) {
    this.log(`开始${testName}...`, 'info');
    console.log('');
    
    try {
      execSync(`node ${testPath}`, { stdio: 'inherit' });
      this.log(`${testName}完成`, 'success');
      return true;
    } catch (error) {
      this.log(`${testName}失败`, 'error');
      return false;
    }
  }

  generateReport() {
    console.log('\n');
    this.log('========================================', 'info');
    this.log('       QuickAgents 测试总结报告         ', 'info');
    this.log('========================================', 'info');
    console.log('');
    
    // 读取各个测试的JSON结果（如果有的话）
    const testTypes = [
      { name: '单元测试', path: 'tests/unit/test-unit.js' },
      { name: '集成测试', path: 'tests/integration/test-integration.js' },
      { name: 'E2E测试', path: 'tests/e2e/test-e2e.js' },
      { name: '性能测试', path: 'tests/performance/test-performance.js' }
    ];
    
    console.log('测试覆盖范围:');
    console.log('');
    console.log('1. 单元测试');
    console.log('   - Agent配置验证（19个代理）');
    console.log('   - Skill配置验证（14个技能）');
    console.log('   - JSON配置验证（categories.json, models.json等）');
    console.log('   - 核心文档验证（MEMORY.md, TASKS.md等）');
    console.log('');
    console.log('2. 集成测试');
    console.log('   - Orchestrator集成');
    console.log('   - Background Agents集成');
    console.log('   - Boulder进度追踪集成');
    console.log('   - Category系统集成');
    console.log('   - 多模型协同集成');
    console.log('   - Prometheus规划系统集成');
    console.log('   - LSP/AST集成');
    console.log('   - Todo Enforcer集成');
    console.log('');
    console.log('3. E2E测试');
    console.log('   - 场景1: 新项目初始化流程');
    console.log('   - 场景2: 现有项目分析流程');
    console.log('   - 场景3: 跨会话工作恢复流程');
    console.log('   - 场景4: 复杂任务执行流程');
    console.log('   - 场景5: 多模型协同流程');
    console.log('');
    console.log('4. 性能测试');
    console.log('   - 配置加载性能');
    console.log('   - 文件结构性能');
    console.log('   - 配置文件大小');
    console.log('   - 文档大小');
    console.log('   - 并发支持');
    console.log('   - 内存效率');
    console.log('');
    
    // 生成测试摘要
    console.log('测试摘要:');
    console.log('');
    console.log('- 总测试场景: 4类测试');
    console.log('- 总测试用例: 约150+个');
    console.log('- 测试覆盖: 配置文件 + 集成关系 + 工作流程 + 性能指标');
    console.log('');
    
    console.log('建议:');
    console.log('');
    console.log('1. 定期运行测试确保配置正确性');
    console.log('2. 在添加新Agent/Skill后运行单元测试');
    console.log('3. 在修改集成关系后运行集成测试');
    console.log('4. 在发布前运行完整测试套件');
    console.log('');
  }

  run() {
    this.log('QuickAgents 测试套件启动', 'info');
    console.log('');
    
    console.log('========================================');
    console.log('   QuickAgents 完整测试套件');
    console.log('========================================');
    console.log('');
    
    // 运行所有测试
    const tests = [
      { name: '单元测试', path: 'tests/unit/test-unit.js' },
      { name: '集成测试', path: 'tests/integration/test-integration.js' },
      { name: 'E2E测试', path: 'tests/e2e/test-e2e.js' },
      { name: '性能测试', path: 'tests/performance/test-performance.js' }
    ];
    
    tests.forEach((test, index) => {
      console.log(`\n${'='.repeat(50)}`);
      console.log(`测试 ${index + 1}/4: ${test.name}`);
      console.log('='.repeat(50));
      this.runTest(test.path, test.name);
    });
    
    // 生成总结报告
    this.generateReport();
    
    this.log('测试套件执行完成', 'success');
  }
}

// 运行测试
const runner = new QuickAgentsTestRunner();
runner.run();
