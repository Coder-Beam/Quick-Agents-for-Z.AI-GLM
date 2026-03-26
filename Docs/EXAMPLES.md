# QuickAgents 示例代码

> 丰富的使用示例与最佳实践

---

## 目录

1. [快速开始示例](#快速开始示例)
2. [代理使用示例](#代理使用示例)
3. [技能使用示例](#技能使用示例)
4. [命令使用示例](#命令使用示例)
5. [配置示例](#配置示例)
6. [完整项目示例](#完整项目示例)

---

## 快速开始示例

### 示例1：第一个QuickAgents项目

**场景**：创建一个新的Vue3项目

**步骤**：

1. 在OpenCode中发送：
```
启动QuickAgent
```

2. 系统检测到新项目，开始12轮需求澄清：

```
## 第1轮询问 - 业务本质

**核心问题**：
1. 这个项目的核心目标是什么？
   - [ ] 学习/练手
   - [ ] 个人项目
   - [ ] 商业项目
   - [ ] 企业内部系统

2. 主要解决什么痛点？

**已确认信息**：
- 项目类型：新项目
- 技术栈：Vue3（待确认）

**待澄清维度**：
- [x] L1 业务本质
- [ ] L2 用户画像
- [ ] L3 核心流程
...
```

3. 完成所有轮次后，系统自动创建：

```
项目根目录/
├── AGENTS.md
├── Docs/
│   ├── MEMORY.md
│   ├── TASKS.md
│   ├── DESIGN.md
│   └── INDEX.md
└── .opencode/
    ├── agents/
    ├── commands/
    └── skills/
```

4. 开始第一个任务：

```
@fenghou-orchestrate 实现用户登录功能
```

### 示例2：现有项目集成

**场景**：为现有React项目添加QuickAgents

**步骤**：

1. 复制配置：
```bash
# 克隆QuickAgents
git clone https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM.git

# 复制到你的项目
cp -r Quick-Agents-for-Z.AI-GLM/.opencode your-project/
cp Quick-Agents-for-Z.AI-GLM/AGENTS.md your-project/
```

2. 在OpenCode中发送：
```
启动QuickAgent
```

3. 系统检测到现有项目，询问意图：

```
检测到现有项目：
- 技术栈：React + TypeScript
- 依赖：已安装（package.json存在）
- 文档：部分存在

请选择：
- [ ] 继续开发（推荐）
- [ ] 重新开始
- [ ] 功能增强
```

4. 选择"继续开发"后，系统读取现有代码并继续工作。

---

## 代理使用示例

### 示例1：使用yinglong-init

**场景**：初始化一个Node.js API项目

```
@yinglong-init 初始化一个Express + TypeScript的REST API项目
```

**输出**：

```markdown
## 项目初始化报告

### 项目信息
- 名称：my-api
- 类型：Node.js REST API
- 技术栈：Express + TypeScript

### 已创建文件
1. `package.json` - 项目配置
2. `tsconfig.json` - TypeScript配置
3. `src/index.ts` - 入口文件
4. `src/routes/` - 路由目录
5. `Docs/MEMORY.md` - 项目记忆
6. `Docs/TASKS.md` - 任务清单

### 下一步建议
1. 安装依赖：`npm install`
2. 开发模式：`npm run dev`
3. 查看任务：`Docs/TASKS.md`
```

### 示例2：使用boyi-consult

**场景**：分析用户管理模块需求

```
@boyi-consult 分析用户管理模块的需求，包括注册、登录、权限管理
```

**输出**：

```markdown
## 需求分析报告

### 模块概述
用户管理模块负责系统的用户认证、授权和管理。

### 功能清单

#### 1. 用户注册
- **输入**：用户名、邮箱、密码
- **验证**：邮箱格式、密码强度
- **输出**：注册成功/失败
- **异常**：邮箱已存在、用户名重复

#### 2. 用户登录
- **输入**：用户名/邮箱、密码
- **验证**：凭证正确性
- **输出**：JWT Token
- **异常**：凭证错误、账户锁定

#### 3. 权限管理
- **角色**：管理员、普通用户、访客
- **权限**：基于角色的访问控制（RBAC）
- **操作**：角色分配、权限查询

### 数据模型

```typescript
interface User {
  id: string;
  username: string;
  email: string;
  password_hash: string;
  role: UserRole;
  created_at: Date;
  updated_at: Date;
}

enum UserRole {
  ADMIN = 'admin',
  USER = 'user',
  GUEST = 'guest'
}
```

### 技术建议
1. 使用bcrypt进行密码哈希
2. JWT用于会话管理
3. Redis用于Token黑名单
```

### 示例3：使用jianming-review

**场景**：审查认证代码

```
@jianming-review 审查src/auth/login.ts文件
```

**输出**：

```markdown
## 代码审查报告

### 概览
- 文件：src/auth/login.ts
- 行数：156
- 问题数：5（严重：1，警告：2，建议：2）

### 严重问题

#### 1. [行45] SQL注入风险
```typescript
// 问题代码
const query = `SELECT * FROM users WHERE email = '${email}'`;

// 建议修复
const query = 'SELECT * FROM users WHERE email = ?';
db.query(query, [email]);
```

### 警告

#### 2. [行78] 密码比较未使用恒定时间算法
```typescript
// 问题代码
if (password === user.password_hash) { ... }

// 建议修复
if (await bcrypt.compare(password, user.password_hash)) { ... }
```

#### 3. [行102] 缺少速率限制
建议添加登录速率限制，防止暴力破解。

### 建议

#### 4. [行34] 可提取为配置
JWT密钥应从环境变量读取。

#### 5. [行89] 可添加日志
建议添加登录成功/失败的日志记录。
```

### 示例4：使用fenghou-orchestrate

**场景**：完成复杂任务

```
@fenghou-orchestrate 实现完整的用户认证系统，包括注册、登录、密码重置
```

**输出**：

```markdown
## 任务分解报告

### 主任务
实现完整的用户认证系统

### 子任务（共8个）

#### 阶段1：基础架构（串行）
1. [T001] 设计数据模型
   - 代理：@boyi-consult
   - 预计时间：30分钟

2. [T002] 创建数据库表
   - 代理：@huodi-deps
   - 预计时间：20分钟

#### 阶段2：核心功能（可并行）
3. [T003] 实现注册功能
   - 代理：@yinglong-init
   - 依赖：T002
   - 预计时间：1小时

4. [T004] 实现登录功能
   - 代理：@yinglong-init
   - 依赖：T002
   - 预计时间：1小时

5. [T005] 实现密码重置
   - 代理：@yinglong-init
   - 依赖：T002
   - 预计时间：1小时

#### 阶段3：质量保证（串行）
6. [T006] 编写单元测试
   - 代理：@lishou-test
   - 依赖：T003, T004, T005
   - 预计时间：2小时

7. [T007] 代码审查
   - 代理：@jianming-review
   - 依赖：T006
   - 预计时间：30分钟

8. [T008] 安全审计
   - 代理：@mengzhang-security
   - 依赖：T007
   - 预计时间：30分钟

### 执行计划
- 总预计时间：6.5小时
- 并行度：最高3个任务
- 关键路径：T001 → T002 → T003/004/005 → T006 → T007 → T008

开始执行？[Y/n]
```

---

## 技能使用示例

### 示例1：使用inquiry-skill

**场景**：12轮需求澄清

**触发**：
```
启动QuickAgent
```

**过程**：

```markdown
## 第1轮询问 - 业务本质

**核心问题**：
1. 这个项目的核心目标是什么？
2. 主要解决什么痛点？
3. 成功指标是什么？

**已确认信息**：
（暂无）

**待澄清维度**：
- [ ] L1 业务本质 ← 当前
- [ ] L2 用户画像
- [ ] L3 核心流程
- [ ] L4 功能清单
- [ ] L5 数据模型
- [ ] L6 技术栈
- [ ] L7 交付标准
- [ ] L8 风险评估
- [ ] L9 性能要求
- [ ] L10 安全要求
- [ ] L11 扩展性
- [ ] L12 维护性

---

用户回答：
1. 核心目标：开发一个在线教育平台
2. 痛点：现有平台价格高、互动性差
3. 成功指标：3个月内上线，6个月达到1000用户

---

## 第2轮询问 - 用户画像

**核心问题**：
1. 目标用户是谁？
   - 年龄段？
   - 技术水平？
   - 使用场景？

**已确认信息**：
- 核心目标：在线教育平台
- 痛点：价格高、互动性差
- 成功指标：3个月上线，6个月1000用户

**待澄清维度**：
- [x] L1 业务本质
- [ ] L2 用户画像 ← 当前
...

（继续12轮...）
```

### 示例2：使用tdd-workflow-skill

**场景**：TDD开发用户验证功能

**步骤1：Red（编写失败的测试）**

```typescript
// tests/auth/validate.test.ts
import { validateUser } from '@/auth/validate';

describe('validateUser', () => {
  it('should return valid for correct user data', () => {
    const user = {
      email: 'test@example.com',
      password: 'Password123!'
    };
    
    const result = validateUser(user);
    
    expect(result.valid).toBe(true);
    expect(result.errors).toHaveLength(0);
  });

  it('should return invalid for invalid email', () => {
    const user = {
      email: 'invalid-email',
      password: 'Password123!'
    };
    
    const result = validateUser(user);
    
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('Invalid email format');
  });
});
```

**运行测试**：
```bash
npm test
# FAIL: validateUser is not defined
```

**步骤2：Green（编写最少代码通过测试）**

```typescript
// src/auth/validate.ts
export interface UserInput {
  email: string;
  password: string;
}

export interface ValidationResult {
  valid: boolean;
  errors: string[];
}

export function validateUser(user: UserInput): ValidationResult {
  const errors: string[] = [];
  
  // 邮箱验证
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(user.email)) {
    errors.push('Invalid email format');
  }
  
  return {
    valid: errors.length === 0,
    errors
  };
}
```

**运行测试**：
```bash
npm test
# PASS: All tests passed
```

**步骤3：Refactor（重构优化）**

```typescript
// src/auth/validate.ts
import { validator } from '@/utils/validator';

export interface UserInput {
  email: string;
  password: string;
}

export interface ValidationResult {
  valid: boolean;
  errors: string[];
}

export function validateUser(user: UserInput): ValidationResult {
  const errors: string[] = [];
  
  // 使用统一的验证工具
  if (!validator.isEmail(user.email)) {
    errors.push('Invalid email format');
  }
  
  if (!validator.isStrongPassword(user.password)) {
    errors.push('Password does not meet strength requirements');
  }
  
  return {
    valid: errors.length === 0,
    errors
  };
}
```

**运行测试**：
```bash
npm test
# PASS: All tests still passed
```

### 示例3：使用git-commit-skill

**场景**：完成任务后自动生成提交信息

**操作**：
```bash
# 完成任务后
git add .

# 系统自动触发git-commit-skill
# 生成提交信息：
```

**自动生成的提交信息**：
```
feat(auth): implement user validation with TDD

- Add validateUser function with email and password validation
- Create comprehensive unit tests (100% coverage)
- Refactor to use unified validator utility

Closes #T003

Test: npm test
Docs: Docs/features/auth/VALIDATION.md
```

### 示例4：使用multi-model-skill

**场景**：复杂架构设计任务

**触发**：
```
@fenghou-orchestrate 设计一个高并发的订单系统架构
```

**系统自动选择Category**：

```json
{
  "detected_category": "ultrabrain",
  "reason": "包含关键词：架构、设计、高并发",
  "selected_model": "gpt-5.4",
  "fallback_chain": ["glm-5-plus", "gemini-2.0-flash"]
}
```

**执行日志**：
```
[INFO] Category detected: ultrabrain
[INFO] Primary model: gpt-5.4
[INFO] Task started: 架构设计
[INFO] Using gpt-5.4 for deep reasoning
[INFO] Analysis complete
[INFO] Generated architecture document
[SUCCESS] Task completed successfully
```

---

## 命令使用示例

### 示例1：使用ultrawork命令

**场景**：一键完成复杂任务

```bash
/ultrawork 实现用户认证系统，包括JWT、刷新Token、密码重置
```

**执行过程**：

```
[START] Ultrawork: 实现用户认证系统

[STEP 1] 任务分解
├─ T001: 设计认证架构
├─ T002: 实现JWT生成和验证
├─ T003: 实现刷新Token机制
├─ T004: 实现密码重置功能
├─ T005: 编写单元测试
└─ T006: 安全审查

[STEP 2] 依赖分析
├─ T001 (无依赖)
├─ T002 → 依赖 T001
├─ T003 → 依赖 T002
├─ T004 → 依赖 T002
├─ T005 → 依赖 T003, T004
└─ T006 → 依赖 T005

[STEP 3] 并行执行（并发度：3）
├─ [RUNNING] T001: 设计认证架构
│   └─ [DONE] 完成 (5分钟)
├─ [RUNNING] T002: 实现JWT (并行)
├─ [RUNNING] T003: 实现刷新Token (等待T002)
└─ [RUNNING] T004: 实现密码重置 (等待T002)

[STEP 4] 结果汇总
├─ 创建文件：12个
├─ 编写测试：8个
├─ 测试覆盖率：92%
└─ 安全评分：95/100

[COMPLETE] 总耗时：2小时15分钟
```

### 示例2：使用start-work命令

**场景**：跨会话恢复工作

**上次会话结束时**：
```json
// .quickagents/boulder.json
{
  "session_id": "abc-123",
  "completed_tasks": 5,
  "total_tasks": 8,
  "current_task": "T006",
  "notepad": {
    "learnings": [
      {
        "timestamp": "2026-03-25T10:30:00Z",
        "content": "JWT刷新Token需要存储在Redis中"
      }
    ]
  }
}
```

**新会话开始**：
```bash
/start-work
```

**输出**：
```
[RECOVER] 恢复工作会话

[INFO] 会话ID：abc-123
[INFO] 完成进度：5/8 (62%)
[INFO] 当前任务：T006 - 编写单元测试

[LEARNINGS] 上次会话的学习点：
1. JWT刷新Token需要存储在Redis中
2. 密码重置链接有效期为24小时

[RESUME] 继续执行任务 T006...

[CURRENT] 正在编写单元测试
├─ 已完成：auth.test.ts
├─ 进行中：jwt.test.ts
└─ 待完成：refresh.test.ts, reset.test.ts

继续工作？[Y/n]
```

---

## 配置示例

### 示例1：自定义Category

**场景**：添加新的Category用于数据分析任务

**配置**：`.opencode/config/categories.json`

```json
{
  "categories": {
    "data-analysis": {
      "description": "数据分析、统计、可视化任务",
      "primary": "gpt-5.4",
      "fallback": ["glm-5-plus"],
      "keywords": ["分析", "统计", "数据", "可视化", "图表"],
      "file_patterns": ["*.py", "*.ipynb", "*.sql"]
    }
  }
}
```

### 示例2：自定义模型配置

**场景**：配置自定义的模型路由

**配置**：`.opencode/config/models.json`

```json
{
  "models": {
    "glm-5": {
      "provider": "zhipu",
      "model_id": "glm-5",
      "max_tokens": 8192,
      "temperature": 0.7,
      "cost_per_1k_tokens": 0.001,
      "capabilities": ["reasoning", "coding", "planning"]
    },
    "glm-5-flash": {
      "provider": "zhipu",
      "model_id": "glm-5-flash",
      "max_tokens": 4096,
      "temperature": 0.5,
      "cost_per_1k_tokens": 0.0001,
      "capabilities": ["quick_response", "formatting"]
    }
  },
  "routing": {
    "default_category": "quick",
    "fallback_chain": ["glm-5", "gpt-4o-mini"],
    "load_balancing": {
      "strategy": "weighted",
      "weights": {
        "glm-5": 0.6,
        "gpt-5.4": 0.3,
        "gemini-2.0-flash": 0.1
      }
    }
  }
}
```

### 示例3：自定义代理

**场景**：创建一个专门处理API文档的代理

**配置**：`.opencode/agents/api-doc-writer.md`

```yaml
---
description: API文档编写专家，专注于OpenAPI/Swagger文档生成
mode: subagent
model: glm-5
temperature: 0.2
tools:
  write: true
  edit: true
  bash: false
permission:
  edit: allow
  bash:
    "*": deny
---

# API Doc Writer Agent

## 职责

专门负责API文档的编写和维护：

1. OpenAPI 3.0规范文档生成
2. Swagger UI集成
3. API示例代码生成
4. 文档同步更新

## 工作流程

### 阶段1：API分析
1. 扫描API路由文件
2. 提取路由、参数、响应信息
3. 识别认证要求

### 阶段2：文档生成
1. 生成OpenAPI YAML/JSON
2. 添加详细描述和示例
3. 生成多语言示例代码

### 阶段3：集成与测试
1. 集成Swagger UI
2. 测试API文档可访问性
3. 验证示例代码正确性

## 输出格式

```yaml
openapi: 3.0.0
info:
  title: API名称
  version: 1.0.0
paths:
  /api/users:
    get:
      summary: 获取用户列表
      parameters:
        - name: page
          in: query
          schema:
            type: integer
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserList'
```
```

---

## 完整项目示例

### 示例1：电商API项目

**项目结构**：

```
ecommerce-api/
├── AGENTS.md
├── Docs/
│   ├── MEMORY.md
│   ├── TASKS.md
│   ├── DESIGN.md
│   ├── INDEX.md
│   └── features/
│       ├── auth/
│       │   ├── MEMORY.md
│       │   ├── TASKS.md
│       │   └── DESIGN.md
│       ├── products/
│       └── orders/
├── .opencode/
│   ├── agents/
│   ├── commands/
│   ├── skills/
│   └── config/
│       ├── categories.json
│       └── models.json
├── .quickagents/
│   └── boulder.json
├── src/
│   ├── modules/
│   │   ├── auth/
│   │   ├── products/
│   │   └── orders/
│   └── index.ts
└── tests/
    ├── unit/
    ├── integration/
    └── e2e/
```

**使用流程**：

1. **初始化项目**
```
启动QuickAgent
```

2. **完成12轮需求澄清**
（输出详细的需求文档）

3. **开始开发**
```
@fenghou-orchestrate 实现用户认证模块
@fenghou-orchestrate 实现商品管理模块
@fenghou-orchestrate 实现订单处理模块
```

4. **跨会话工作**
```bash
# 每天开始工作时
/start-work

# 每天结束工作时
# 系统自动保存boulder.json
```

5. **质量保证**
```
@jianming-review 审查所有代码
@lishou-test 运行所有测试
@mengzhang-security 进行安全审计
```

### 示例2：React前端项目

**使用示例**：

```
@fenghou-orchestrate 实现用户Dashboard页面

[任务分解]
├─ 设计Dashboard布局
├─ 创建统计卡片组件
├─ 实现图表展示
├─ 添加数据刷新功能
└─ 编写E2E测试

[自动选择Category]
检测到：visual-engineering
使用模型：gemini-2.0-flash
（适合UI开发任务）
```

---

## 附录

### 常见问题

#### Q1：如何查看当前项目进度？
```bash
cat .quickagents/boulder.json
```

#### Q2：如何跳过某些询问轮次？
```
在第N轮时回复：跳过 或 足够了
```

#### Q3：如何手动触发技能？
```
目前技能主要通过代理间接调用。
直接调用功能正在开发中。
```

#### Q4：如何添加自定义代理？
1. 在`.opencode/agents/`创建`.md`文件
2. 按照规范编写YAML Front Matter
3. 重启OpenCode

### 更多示例

- **GitHub仓库**: https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM
- **示例项目**: `/examples`目录
- **视频教程**: 待发布

---

*文档版本: v1.0 | 更新时间: 2026-03-25*
