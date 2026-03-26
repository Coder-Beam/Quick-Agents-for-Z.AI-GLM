# QuickAgents Installation Guide

> Complete guide for installing and configuring QuickAgents

---

## Table of Contents

- [For Humans](#for-humans)
- [For LLM Agents](#for-llm-agents)
- [Installation Steps](#installation-steps)
- [Configuration](#configuration)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

---

## For Humans

Copy and paste this prompt into your AI agent (OpenCode CLI/Desktop, etc.):

```
Install and configure QuickAgents by following the instructions here:
https://raw.githubusercontent.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/main/Docs/en/guide/installation.md
```

**Or use CLI for one-line installation:**

```bash
npm install -g quickagents-cli
qa init
```

> **Tip**: Let AI agents handle the installation - it's the easiest way to avoid manual configuration errors.

---

## For LLM Agents

> **IMPORTANT: Use `curl` to fetch this file, NOT WebFetch.** WebFetch summarizes content and loses critical details.

```bash
curl -fsSL https://raw.githubusercontent.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/main/Docs/en/guide/installation.md
```

If you're an LLM Agent helping set up QuickAgents, welcome! You'll now help your user install the best AI agent project initialization system. Tell the user: **"QAQAQAQAQA... 🎉 Let's start installing QuickAgents!"**

Please follow these steps:

---

## Installation Steps

### Step 0: Environment Check

First check the user's environment:

```bash
# Check if OpenCode is installed
if command -v opencode &> /dev/null; then
    echo "✅ OpenCode installed: $(opencode --version)"
else
    echo "❌ OpenCode not installed"
fi

# Check Node.js (optional, for CLI)
if command -v node &> /dev/null; then
    echo "✅ Node.js installed: $(node --version)"
else
    echo "⚠️ Node.js not installed (optional, CLI only)"
fi

# Check Git
if command -v git &> /dev/null; then
    echo "✅ Git installed"
else
    echo "❌ Git not installed"
fi
```

**If OpenCode is not installed**:
- Please install OpenCode first: https://opencode.ai/docs
- Continue after installation

---

### Step 1: Ask About Subscriptions

Ask the user these questions to determine configuration options:

1. **Do you have a Z.ai Coding Plan subscription?**
   - If **yes** → Use GLM-5 models
   - If **no** → Need to configure other models

2. **Do you have an OpenCode Go subscription?**
   - OpenCode Go is a $10/month subscription providing access to GLM-5, Kimi K2.5, and MiniMax M2.7 models
   - If **yes** → Can use GLM series models
   - If **no** → Need to configure other models

3. **Do you have a Claude Pro/Max subscription?**
   - If **yes** → Can configure Claude models as backup
   - If **no** → Use GLM series only

4. **Do you have an OpenAI/ChatGPT Plus subscription?**
   - If **yes** → Can configure GPT models as backup
   - If **no** → Use GLM series only

5. **What is your primary development language?** (Multiple selection)
   - TypeScript/JavaScript
   - Python
   - Rust
   - Go
   - Java
   - C/C++
   - Other

---

### Step 2: Download QuickAgents

**Method 1: Git Clone (Recommended)**

```bash
# Navigate to project directory
cd /path/to/your/project

# Clone QuickAgents
git clone https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM.git .quickagents-temp

# Copy necessary files
cp -r .quickagents-temp/.opencode ./
cp .quickagents-temp/AGENTS.md ./

# Clean up temp files
rm -rf .quickagents-temp

echo "✅ QuickAgents files copied"
```

**Method 2: curl Download (No Git environment)**

```bash
# Create temp directory
mkdir -p .quickagents-temp

# Download core files
curl -fsSL https://raw.githubusercontent.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/main/AGENTS.md -o AGENTS.md

# Download .opencode directory
curl -fsSL https://codeload.github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/tar.gz/main | tar -xz --strip-components=1 Quick-Agents-for-Z.AI-GLM/.opencode

echo "✅ QuickAgents files downloaded"
```

---

### Step 3: Configure models.json

Based on user's subscription, generate `.opencode/config/models.json`:

**Scenario A: Z.ai Coding Plan Only**

```json
{
  "version": "2.0.1",
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

**Scenario B: OpenCode Go Subscription**

```json
{
  "version": "2.0.1",
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

**Scenario C: Claude + OpenCode Go**

```json
{
  "version": "2.0.1",
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

### Step 4: Configure lsp-config.json

Based on user's development language, generate `.opencode/config/lsp-config.json`:

**Single Language (TypeScript)**

```json
{
  "version": "2.0.1",
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

**Multi-Language**

```json
{
  "version": "2.0.1",
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

### Step 5: Create Docs Directory

```bash
# Create docs directory
mkdir -p Docs

# Create necessary doc files
touch Docs/MEMORY.md
touch Docs/TASKS.md
touch Docs/DESIGN.md
touch Docs/INDEX.md
touch Docs/DECISIONS.md

echo "✅ Documentation directory created"
```

---

### Step 6: Verify Installation

```bash
# Check file structure
echo "Checking installation..."
test -f AGENTS.md && echo "✅ AGENTS.md"
test -d .opencode && echo "✅ .opencode/"
test -d .opencode/agents && echo "✅ .opencode/agents/"
test -d .opencode/skills && echo "✅ .opencode/skills/"
test -d Docs && echo "✅ Docs/"
test -f .opencode/config/models.json && echo "✅ models.json"
test -f .opencode/config/lsp-config.json && echo "✅ lsp-config.json"
```

---

### Step 7: Start Using

Congratulations! 🎉 QuickAgents has been successfully installed!

Now you can start using:

```
启动QuickAgent
```

**Or use other trigger words**:
- `启动QuickAgents`
- `启动QA`
- `Start QA`

---

## Configuration

### Configuration Files

| File | Location | Purpose |
|------|----------|---------|
| models.json | `.opencode/config/models.json` | AI model configuration |
| lsp-config.json | `.opencode/config/lsp-config.json` | LSP server configuration |
| quickagents.json | `.opencode/config/quickagents.json` | QuickAgents main config |
| categories.json | `.opencode/config/categories.json` | Task classification config |

### Modifying Configuration

You can modify configuration files at any time:

```bash
# Edit model configuration
vim .opencode/config/models.json

# Edit LSP configuration
vim .opencode/config/lsp-config.json
```

---

## Verification

### Quick Check

```bash
# Check trigger words
grep "triggerWords" .opencode/config/quickagents.json

# Check agents
ls .opencode/agents/

# Check skills
ls .opencode/skills/
```

### Functional Test

```
启动QuickAgent
```

If the system starts the initialization process correctly, the installation is successful.

---

## Troubleshooting

### Issue 1: OpenCode doesn't recognize AGENTS.md

**Solution**:
```bash
# Ensure AGENTS.md is in project root
ls -la AGENTS.md

# Ensure correct file encoding
file AGENTS.md  # Should show: UTF-8 Unicode text
```

### Issue 2: Agents won't start

**Solution**:
```bash
# Check .opencode directory structure
ls -la .opencode/agents/
ls -la .opencode/skills/

# Validate JSON configs
cat .opencode/config/models.json | python -m json.tool
```

### Issue 3: Model invocation fails

**Solution**:
1. Check if models.json is configured correctly
2. Confirm subscription status is valid
3. Try using fallback models

---

## Next Steps

1. **Read User Guide**: `Docs/en/USER_GUIDE.md`
2. **Learn about Agents**: `Docs/en/AGENT_GUIDE.md`
3. **Understand Architecture**: `Docs/en/ARCHITECTURE.md`

---

*Version: 2.0.1 | Last Updated: 2026-03-26*
