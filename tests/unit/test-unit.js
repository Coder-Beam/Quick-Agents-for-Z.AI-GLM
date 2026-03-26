#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

class QuickAgentsUnitTester {
  constructor() {
    this.results = {
      total: 0,
      passed: 0,
      failed: 0,
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

  validateAgentConfig(filepath) {
    const content = fs.readFileSync(filepath, 'utf-8');
    const filename = path.basename(filepath);
    
    // 测试1: 文件存在
    this.test(`[${filename}] 文件存在`, fs.existsSync(filepath));
    
    // 测试2: YAML Front Matter存在
    const hasYAML = content.includes('---') && content.split('---').length >= 3;
    this.test(`[${filename}] YAML Front Matter存在`, hasYAML);
    
    if (hasYAML) {
      const yamlPart = content.split('---')[1];
      
      // 测试3: description字段
      const hasDesc = yamlPart.includes('description:');
      this.test(`[${filename}] description字段存在`, hasDesc);
      
      // 测试4: mode字段
      const hasMode = yamlPart.includes('mode:');
      this.test(`[${filename}] mode字段存在`, hasMode);
      
      // 测试5: model字段
      const hasModel = yamlPart.includes('model:');
      this.test(`[${filename}] model字段存在`, hasModel);
      
      // 测试6: tools字段
      const hasTools = yamlPart.includes('tools:');
      this.test(`[${filename}] tools字段存在`, hasTools);
    }
    
    // 测试7: 文件大小合理（>500字节）
    const size = fs.statSync(filepath).size;
    this.test(`[${filename}] 文件大小合理`, size > 500, `(${size} bytes)`);
  }

  validateSkillConfig(skillPath) {
    const skillMdPath = path.join(skillPath, 'SKILL.md');
    const skillName = path.basename(skillPath);
    
    // 测试1: SKILL.md存在
    this.test(`[${skillName}] SKILL.md存在`, fs.existsSync(skillMdPath));
    
    if (fs.existsSync(skillMdPath)) {
      const content = fs.readFileSync(skillMdPath, 'utf-8');
      
      // 测试2: 功能说明
      const hasDescription = content.includes('## 功能说明') || content.includes('# ') ;
      this.test(`[${skillName}] 功能说明存在`, hasDescription);
      
      // 测试3: 使用场景
      const hasUsage = content.includes('## 使用') || content.includes('## 工作');
      this.test(`[${skillName}] 使用场景存在`, hasUsage);
      
      // 测试4: 文件大小合理
      const size = fs.statSync(skillMdPath).size;
      this.test(`[${skillName}] 文件大小合理`, size > 300, `(${size} bytes)`);
    }
  }

  validateJSONConfig(filepath) {
    const filename = path.basename(filepath);
    
    // 测试1: 文件存在
    this.test(`[${filename}] 文件存在`, fs.existsSync(filepath));
    
    if (fs.existsSync(filepath)) {
      try {
        const content = JSON.parse(fs.readFileSync(filepath, 'utf-8'));
        
        // 测试2: JSON有效
        this.test(`[${filename}] JSON格式有效`, true);
        
        // 测试3: 非空对象
        this.test(`[${filename}] 配置非空`, Object.keys(content).length > 0);
        
      } catch (error) {
        this.test(`[${filename}] JSON格式有效`, false, error.message);
      }
    }
  }

  run() {
    this.log('开始单元测试...', 'info');
    console.log('');
    
    // 1. 测试Agent配置
    this.log('=== 测试Agent配置 ===', 'info');
    const agentsDir = '.opencode/agents';
    const agentFiles = fs.readdirSync(agentsDir)
      .filter(f => f.endsWith('.md') && f !== 'README.md');
    
    agentFiles.forEach(file => {
      this.validateAgentConfig(path.join(agentsDir, file));
    });
    
    console.log('');
    
    // 2. 测试Skill配置
    this.log('=== 测试Skill配置 ===', 'info');
    const skillsDir = '.opencode/skills';
    const skillDirs = fs.readdirSync(skillsDir, { withFileTypes: true })
      .filter(d => d.isDirectory() && !d.name.startsWith('.'))
      .map(d => d.name);
    
    skillDirs.forEach(skillName => {
      this.validateSkillConfig(path.join(skillsDir, skillName));
    });
    
    console.log('');
    
    // 3. 测试JSON配置
    this.log('=== 测试JSON配置 ===', 'info');
    const configDir = '.opencode/config';
    if (fs.existsSync(configDir)) {
      const jsonFiles = fs.readdirSync(configDir).filter(f => f.endsWith('.json'));
      jsonFiles.forEach(file => {
        this.validateJSONConfig(path.join(configDir, file));
      });
    }
    
    console.log('');
    
    // 4. 测试核心文档
    this.log('=== 测试核心文档 ===', 'info');
    const docsDir = 'Docs';
    const requiredDocs = ['MEMORY.md', 'TASKS.md', 'DESIGN.md', 'INDEX.md', 'USER_GUIDE.md', 'API_REFERENCE.md', 'EXAMPLES.md'];
    
    requiredDocs.forEach(doc => {
      const docPath = path.join(docsDir, doc);
      this.test(`[${doc}] 文档存在`, fs.existsSync(docPath));
      
      if (fs.existsSync(docPath)) {
        const size = fs.statSync(docPath).size;
        this.test(`[${doc}] 文档非空`, size > 100, `(${size} bytes)`);
      }
    });
    
    // 生成报告
    console.log('');
    this.log('=== 单元测试报告 ===', 'info');
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
const tester = new QuickAgentsUnitTester();
const results = tester.run();

// 返回退出码
process.exit(results.failed > 0 ? 1 : 0);
