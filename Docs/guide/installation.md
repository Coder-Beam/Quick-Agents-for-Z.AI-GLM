# QuickAgents 安装指南

## For Humans（给用户）

复制以下提示词，粘贴到你的AI代理（OpenCode CLI/Desktop等）：

```
Install and configure QuickAgents by following the instructions here:
https://raw.githubusercontent.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/main/Docs/guide/installation.md
```

**或者使用CLI一键安装**（需要Node.js）：

```bash
pip install quickagents
qa init
```

> **提示**：让AI代理来完成安装是最简单的方式，避免手动配置错误。

---

## For LLM Agents（给AI代理）

> **重要：使用 `curl` 获取此文件，而不是 WebFetch。** WebFetch 会总结内容并丢失关键细节。

```bash
curl -fsSL https://raw.githubusercontent.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/main/Docs/guide/installation.md
```

如果你是帮助用户安装QuickAgents的LLM代理，欢迎！你现在将帮助用户安装最好的AI代理项目初始化系统。告诉用户：**"QAQAQAQAQA... 🎉 让我们开始安装QuickAgents！"**

请按以下步骤操作：

---

### Step 0: 检查环境

首先检查用户的环境：

```bash
# 检查是否已安装OpenCode
if command -v opencode &> /dev/null; then
    echo "✅ OpenCode 已安装: $(opencode --version)"
else
    echo "❌ OpenCode 未安装"
fi

# 检查Node.js（可选，用于CLI）
if command -v node &> /dev/null; then
    echo "✅ Node.js 已安装: $(node --version)"
else
    echo "⚠️ Node.js 未安装（可选，仅CLI需要）"
fi

# 检查Git
if command -v git &> /dev/null; then
    echo "✅ Git 已安装"
else
    echo "❌ Git 未安装"
fi
```

**如果OpenCode未安装**：
- 请先安装OpenCode：https://opencode.ai/docs
- 安装完成后继续

---

### Step 1: 询问用户订阅情况

询问用户以下问题以确定配置选项：

1. **你有Z.ai Coding Plan订阅吗？**
   - 如果**是** → 使用GLM-5模型
   - 如果**否** → 需要配置其他模型

2. **你有OpenCode Go订阅吗？**
   - OpenCode Go是$10/月的订阅，提供GLM-5、Kimi K2.5和MiniMax M2.7模型
   - 如果**是** → 可以使用GLM系列模型
   - 如果**否** → 需要配置其他模型

3. **你有Claude Pro/Max订阅吗？**
   - 如果**是** → 可以配置Claude模型作为备选
   - 如果**否** → 仅使用GLM系列

4. **你有OpenAI/ChatGPT Plus订阅吗？**
   - 如果**是** → 可以配置GPT模型作为备选
   - 如果**否** → 仅使用GLM系列

5. **你的主要开发语言是什么？**（可多选）
   - TypeScript/JavaScript
   - Python
   - Rust
   - Go
   - Java
   - C/C++
   - 其他

---

### Step 2: 下载QuickAgents

**方式1：使用Git克隆（推荐）**

```bash
# 进入项目目录
cd /path/to/your/project

# 克隆QuickAgents
git clone https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM.git .quickagents-temp

# 复制必要文件
cp -r .quickagents-temp/.opencode ./
cp .quickagents-temp/AGENTS.md ./

# 清理临时文件
rm -rf .quickagents-temp

echo "✅ QuickAgents文件已复制"
```

**方式2：使用curl下载（无Git环境）**

```bash
# 创建临时目录
mkdir -p .quickagents-temp

# 下载核心文件
curl -fsSL https://raw.githubusercontent.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/main/AGENTS.md -o AGENTS.md

# 下载.opencode目录
curl -fsSL https://codeload.github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/tar.gz/main | tar -xz --strip-components=1 Quick-Agents-for-Z.AI-GLM/.opencode

echo "✅ QuickAgents文件已下载"
```

---

### Step 3: 配置models.json

根据用户的订阅情况，生成 `.opencode/config/models.json`：

**场景A：仅Z.ai Coding Plan**

```json
{
  "version": "2.1.1",
  "primary": "zai-coding-plan/glm-5",
  "categories": {
    "quick": "zai-coding-plan/glm-5-flash",
    "planning": "zai-coding-plan/glm-5",
    "coding": "zai-coding-plan/glm-5",
    "testing": "zai-coding-plan/glm-5-flash",
    "documentation": "zai-coding-plan/glm-5-flash"
  },
  "fallback": []
}
```

**场景B：OpenCode Go订阅**

```json
{
  "version": "2.1.1",
  "primary": "opencode/glm-5",
  "categories": {
    "quick": "opencode/glm-5-flash",
    "planning": "opencode/glm-5",
    "coding": "opencode/glm-5",
    "testing": "opencode/glm-5-flash",
    "documentation": "opencode/glm-5-flash",
    "visual-engineering": "opencode/gemini-2.0-flash",
    "ultrabrain": "opencode/gpt-5.4"
  },
  "fallback": ["opencode/kimi-k2.5", "opencode/minimax-m2.7"]
}
```

**场景C：Claude + OpenCode Go**

```json
{
  "version": "2.1.1",
  "primary": "anthropic/claude-opus-4-6",
  "categories": {
    "quick": "opencode/glm-5-flash",
    "planning": "anthropic/claude-sonnet-4-6",
    "coding": "anthropic/claude-sonnet-4-6",
    "testing": "opencode/glm-5-flash",
    "documentation": "opencode/glm-5-flash",
    "visual-engineering": "opencode/gemini-2.0-flash",
    "ultrabrain": "anthropic/claude-opus-4-6"
  },
  "fallback": ["opencode/glm-5", "opencode/kimi-k2.5"]
}
```

---

### Step 4: 配置lsp-config.json

根据用户的开发语言，生成 `.opencode/config/lsp-config.json`：

**单语言配置（TypeScript）**

```json
{
  "version": "2.1.1",
  "languages": ["typescript"],
  "ast-grep": true,
  "servers": {
    "typescript": {
      "command": "typescript-language-server",
      "args": ["--stdio"]
    }
  }
}
```

**多语言配置**

```json
{
  "version": "2.1.1",
  "languages": ["typescript", "python", "rust"],
  "ast-grep": true,
  "servers": {
    "typescript": {
      "command": "typescript-language-server",
      "args": ["--stdio"]
    },
    "python": {
      "command": "pyright-langserver",
      "args": ["--stdio"]
    },
    "rust": {
      "command": "rust-analyzer",
      "args": []
    }
  }
}
```

---

### Step 5: 创建Docs目录

```bash
# 创建文档目录
mkdir -p Docs

# 创建必要的文档文件
touch Docs/MEMORY.md
touch Docs/TASKS.md
touch Docs/DESIGN.md
touch Docs/INDEX.md
touch Docs/DECISIONS.md

echo "✅ 文档目录已创建"
```

---

### Step 6: 验证安装

```bash
# 检查文件结构
echo "检查安装..."
test -f AGENTS.md && echo "✅ AGENTS.md"
test -d .opencode && echo "✅ .opencode/"
test -d .opencode/agents && echo "✅ .opencode/agents/"
test -d .opencode/skills && echo "✅ .opencode/skills/"
test -d Docs && echo "✅ Docs/"
test -f .opencode/config/models.json && echo "✅ models.json"
test -f .opencode/config/lsp-config.json && echo "✅ lsp-config.json"
```

---

### Step 7: 开始使用

恭喜！🎉 QuickAgents已成功安装！

现在你可以开始使用：

```
启动QuickAgent
```

**或者使用其他触发词**：
- 「启动QuickAgents」
- 「启动QA」
- 「Start QA」

---

## 快速参考

### 触发词
| 触发词 | 说明 |
|--------|------|
| `启动QuickAgent` | 推荐，启动项目初始化 |
| `启动QuickAgents` | 兼容 |
| `启动QA` | 简短 |
| `Start QA` | 英文 |

### 常用命令
| 命令 | 说明 |
|------|------|
| `/start-work` | 跨会话恢复工作 |
| `/ultrawork <任务>` | 超高效执行任务 |
| `@agent-name` | 调用特定代理 |

### 配置文件
| 文件 | 位置 |
|------|------|
| 模型配置 | `.opencode/config/models.json` |
| LSP配置 | `.opencode/config/lsp-config.json` |
| 进度追踪 | `.quickagents/boulder.json` |

---

## 故障排查

### 问题1：OpenCode无法识别AGENTS.md

**解决方案**：
```bash
# 确保AGENTS.md在项目根目录
ls -la AGENTS.md

# 确保文件编码正确
file AGENTS.md  # 应显示: UTF-8 Unicode text
```

### 问题2：代理无法启动

**解决方案**：
```bash
# 检查.opencode目录结构
ls -la .opencode/agents/
ls -la .opencode/skills/

# 验证JSON配置
cat .opencode/config/models.json | python -m json.tool
```

### 问题3：模型调用失败

**解决方案**：
1. 检查models.json配置是否正确
2. 确认订阅状态有效
3. 尝试使用fallback模型

---

## 下一步

1. **阅读用户指南**：`Docs/USER_GUIDE.md`
2. **了解Agent系统**：`Docs/AGENT_GUIDE.md`
3. **查看示例代码**：`Docs/EXAMPLES.md`

---

*文档版本: v2.1.1 | 更新时间: 2026-03-27*
