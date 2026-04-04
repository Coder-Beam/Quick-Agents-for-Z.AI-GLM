#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

class QuickAgentsPerformanceTester {
  constructor() {
    this.results = {
      total: 0,
      passed: 0,
      failed: 0,
      metrics: {},
      errors: []
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

  measureTime(operation, name) {
    const start = process.hrtime.bigint();
    operation();
    const end = process.hrtime.bigint();
    const duration = Number(end - start) / 1_000_000; // 转换为毫秒
    this.results.metrics[name] = duration;
    return duration;
  }

  testConfigLoadingPerformance() {
    this.log('=== 测试配置加载性能 ===', 'info');
    
    // 测试1: Agent配置加载时间
    const agentLoadTime = this.measureTime(() => {
      const agentsDir = '.opencode/agents';
      const files = fs.readdirSync(agentsDir).filter(f => f.endsWith('.md'));
      files.forEach(file => {
        fs.readFileSync(path.join(agentsDir, file), 'utf-8');
      });
    }, 'agent_load_time');
    
    this.test('Agent配置加载时间 < 100ms', agentLoadTime < 100, `(${agentLoadTime.toFixed(2)}ms)`);
    
    // 测试2: Skill配置加载时间
    const skillLoadTime = this.measureTime(() => {
      const skillsDir = '.opencode/skills';
      const dirs = fs.readdirSync(skillsDir, { withFileTypes: true })
        .filter(d => d.isDirectory())
        .map(d => d.name);
      dirs.forEach(skillName => {
        const skillMd = path.join(skillsDir, skillName, 'SKILL.md');
        if (fs.existsSync(skillMd)) {
          fs.readFileSync(skillMd, 'utf-8');
        }
      });
    }, 'skill_load_time');
    
    this.test('Skill配置加载时间 < 100ms', skillLoadTime < 100, `(${skillLoadTime.toFixed(2)}ms)`);
    
    // 测试3: JSON配置加载时间
    const jsonLoadTime = this.measureTime(() => {
      const configDir = '.opencode/config';
      if (fs.existsSync(configDir)) {
        const jsonFiles = fs.readdirSync(configDir).filter(f => f.endsWith('.json'));
        jsonFiles.forEach(file => {
          JSON.parse(fs.readFileSync(path.join(configDir, file), 'utf-8'));
        });
      }
    }, 'json_load_time');
    
    this.test('JSON配置加载时间 < 50ms', jsonLoadTime < 50, `(${jsonLoadTime.toFixed(2)}ms)`);
  }

  testFileStructurePerformance() {
    this.log('=== 测试文件结构性能 ===', 'info');
    
    // 测试1: 目录扫描时间
    const scanTime = this.measureTime(() => {
      const scanDir = (dir) => {
        if (!fs.existsSync(dir)) return;
        const items = fs.readdirSync(dir, { withFileTypes: true });
        items.forEach(item => {
          if (item.isDirectory()) {
            scanDir(path.join(dir, item.name));
          }
        });
      };
      scanDir('.opencode');
      scanDir('Docs');
    }, 'directory_scan_time');
    
    this.test('目录扫描时间 < 50ms', scanTime < 50, `(${scanTime.toFixed(2)}ms)`);
    
    // 测试2: 文件统计时间
    const statsTime = this.measureTime(() => {
      const countFiles = (dir, ext) => {
        if (!fs.existsSync(dir)) return 0;
        let count = 0;
        const items = fs.readdirSync(dir, { withFileTypes: true });
        items.forEach(item => {
          if (item.isDirectory()) {
            count += countFiles(path.join(dir, item.name), ext);
          } else if (item.name.endsWith(ext)) {
            count++;
          }
        });
        return count;
      };
      countFiles('.opencode', '.md');
      countFiles('Docs', '.md');
    }, 'file_stats_time');
    
    this.test('文件统计时间 < 30ms', statsTime < 30, `(${statsTime.toFixed(2)}ms)`);
  }

  testConfigSize() {
    this.log('=== 测试配置文件大小 ===', 'info');
    
    // 测试1: Agent配置总大小
    const agentsDir = '.opencode/agents';
    const agentFiles = fs.readdirSync(agentsDir).filter(f => f.endsWith('.md'));
    let totalAgentSize = 0;
    agentFiles.forEach(file => {
      totalAgentSize += fs.statSync(path.join(agentsDir, file)).size;
    });
    this.results.metrics['total_agent_size'] = totalAgentSize;
    this.test('Agent配置总大小 < 500KB', totalAgentSize < 500 * 1024, `(${(totalAgentSize / 1024).toFixed(2)}KB)`);
    
    // 测试2: Skill配置总大小
    const skillsDir = '.opencode/skills';
    const skillDirs = fs.readdirSync(skillsDir, { withFileTypes: true })
      .filter(d => d.isDirectory())
      .map(d => d.name);
    let totalSkillSize = 0;
    skillDirs.forEach(skillName => {
      const skillMd = path.join(skillsDir, skillName, 'SKILL.md');
      if (fs.existsSync(skillMd)) {
        totalSkillSize += fs.statSync(skillMd).size;
      }
    });
    this.results.metrics['total_skill_size'] = totalSkillSize;
    this.test('Skill配置总大小 < 300KB', totalSkillSize < 300 * 1024, `(${(totalSkillSize / 1024).toFixed(2)}KB)`);
    
    // 测试3: JSON配置总大小
    const configDir = '.opencode/config';
    let totalJsonSize = 0;
    if (fs.existsSync(configDir)) {
      const jsonFiles = fs.readdirSync(configDir).filter(f => f.endsWith('.json'));
      jsonFiles.forEach(file => {
        totalJsonSize += fs.statSync(path.join(configDir, file)).size;
      });
    }
    this.results.metrics['total_json_size'] = totalJsonSize;
    this.test('JSON配置总大小 < 100KB', totalJsonSize < 100 * 1024, `(${(totalJsonSize / 1024).toFixed(2)}KB)`);
  }

  testDocumentationSize() {
    this.log('=== 测试文档大小 ===', 'info');
    
    // 测试1: Docs目录总大小
    const docsDir = 'Docs';
    const docsFiles = fs.readdirSync(docsDir).filter(f => f.endsWith('.md'));
    let totalDocsSize = 0;
    docsFiles.forEach(file => {
      totalDocsSize += fs.statSync(path.join(docsDir, file)).size;
    });
    this.results.metrics['total_docs_size'] = totalDocsSize;
    this.test('Docs目录总大小 < 2MB', totalDocsSize < 2 * 1024 * 1024, `(${(totalDocsSize / 1024).toFixed(2)}KB)`);
    
    // 测试2: 单个文档大小合理
    const maxDocSize = Math.max(...docsFiles.map(f => fs.statSync(path.join(docsDir, f)).size));
    this.results.metrics['max_doc_size'] = maxDocSize;
    this.test('单个文档大小 < 500KB', maxDocSize < 500 * 1024, `(${(maxDocSize / 1024).toFixed(2)}KB)`);
  }

  testConcurrencySupport() {
    this.log('=== 测试并发支持 ===', 'info');
    
    // 测试1: Background Agents配置存在
    const hasBackground = fs.existsSync('.opencode/skills/background-agents-skill/SKILL.md');
    this.test('Background Agents支持', hasBackground);
    
    // 测试2: 并发限制配置
    if (hasBackground) {
      const content = fs.readFileSync('.opencode/skills/background-agents-skill/SKILL.md', 'utf-8');
      const hasConcurrencyConfig = content.includes('并发') || content.includes('concurrent') || content.includes('max');
      this.test('有并发限制配置', hasConcurrencyConfig);
    }
    
    // 测试3: 负载均衡配置
    const hasModelsConfig = fs.existsSync('.opencode/config/models.json');
    if (hasModelsConfig) {
      try {
        const config = JSON.parse(fs.readFileSync('.opencode/config/models.json', 'utf-8'));
        const hasLoadBalancing = config.routing && config.routing.load_balancing;
        this.test('有负载均衡配置', hasLoadBalancing);
      } catch (error) {
        this.test('有负载均衡配置', false, error.message);
      }
    }
  }

  testMemoryEfficiency() {
    this.log('=== 测试内存效率 ===', 'info');
    
    // 测试1: 配置文件数量合理
    const configDir = '.opencode/config';
    let configCount = 0;
    if (fs.existsSync(configDir)) {
      configCount = fs.readdirSync(configDir).filter(f => f.endsWith('.json')).length;
    }
    this.results.metrics['config_file_count'] = configCount;
    this.test('配置文件数量 < 20', configCount < 20, `(${configCount}个)`);
    
    // 测试2: Agent数量合理
    const agentsDir = '.opencode/agents';
    const agentCount = fs.readdirSync(agentsDir).filter(f => f.endsWith('.md') && f !== 'README.md').length;
    this.results.metrics['agent_count'] = agentCount;
    this.test('Agent数量 < 30', agentCount < 30, `(${agentCount}个)`);
    
    // 测试3: Skill数量合理
    const skillsDir = '.opencode/skills';
    const skillCount = fs.readdirSync(skillsDir, { withFileTypes: true })
      .filter(d => d.isDirectory())
      .length;
    this.results.metrics['skill_count'] = skillCount;
    this.test('Skill数量 < 25', skillCount < 25, `(${skillCount}个)`);
  }

  run() {
    this.log('开始性能测试...', 'info');
    console.log('');
    
    // 执行所有性能测试
    this.testConfigLoadingPerformance();
    console.log('');
    
    this.testFileStructurePerformance();
    console.log('');
    
    this.testConfigSize();
    console.log('');
    
    this.testDocumentationSize();
    console.log('');
    
    this.testConcurrencySupport();
    console.log('');
    
    this.testMemoryEfficiency();
    console.log('');
    
    // 生成报告
    this.log('=== 性能测试报告 ===', 'info');
    console.log(`总计: ${this.results.total}`);
    console.log(`通过: ${this.results.passed} ✅`);
    console.log(`失败: ${this.results.failed} ❌`);
    console.log(`成功率: ${((this.results.passed / this.results.total) * 100).toFixed(1)}%`);
    
    console.log('\n性能指标:');
    Object.entries(this.results.metrics).forEach(([key, value]) => {
      if (key.includes('time')) {
        console.log(`- ${key}: ${value.toFixed(2)}ms`);
      } else if (key.includes('size')) {
        console.log(`- ${key}: ${(value / 1024).toFixed(2)}KB`);
      } else {
        console.log(`- ${key}: ${value}`);
      }
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
const tester = new QuickAgentsPerformanceTester();
const results = tester.run();

// 返回退出码
process.exit(results.failed > 0 ? 1 : 0);
