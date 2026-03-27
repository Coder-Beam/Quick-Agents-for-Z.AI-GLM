# QuickAgents User Guide

> Complete user guide for using QuickAgents effectively

---

## Table of Contents

- [Getting Started](#getting-started)
- [Trigger Words](#trigger-words)
- [Commands](#commands)
- [Skills](#skills)
- [Workflows](#workflows)
- [Best Practices](#best-practices)
- [FAQ](#faq)

---

## Getting Started

### Prerequisites

- OpenCode CLI or Desktop installed
- Git installed
- Node.js (optional, for CLI tool)

### First Time Setup

1. Install QuickAgents using one of these methods:

```bash
# Method 1: CLI
npm install -g quickagents-cli
qa init

# Method 2: One-line prompt (recommended)
# Paste into your AI agent:
# Install and configure QuickAgents by following the instructions here:
# https://raw.githubusercontent.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/main/Docs/en/guide/installation.md
```

2. Start the initialization:

```
启动QuickAgent
```

3. Answer the configuration questions (first use only)

4. Complete the requirements inquiry (7 layers)

5. Start developing!

---

## Trigger Words

QuickAgents responds to these trigger words (case-insensitive):

| Trigger Word | Description |
|--------------|-------------|
| `启动QuickAgent` | Recommended, starts project initialization |
| `启动QuickAgents` | Alternative |
| `启动QA` | Short form |
| `Start QA` | English |

### What Happens When Triggered

1. **yinglong-init** agent is invoked
2. Project type is detected (new/existing)
3. Configuration is checked
4. Requirements inquiry begins (if new project)
5. Documentation structure is created
6. Standard agents are created (for programming projects)

---

## Commands

### /start-work

**Purpose**: Cross-session recovery

**Usage**:
```
/start-work
```

**What it does**:
- Reads MEMORY.md to restore context
- Reads boulder.json to restore progress
- Displays current status
- Continues from where you left off

**When to use**:
- Starting a new session
- Recovering from interruption
- Continuing work on a task

---

### /ultrawork

**Purpose**: Ultra-efficient task execution

**Usage**:
```
/ultrawork <task description>
```

**Examples**:
```
/ultrawork Implement user authentication
/ultrawork Fix the login bug
/ultrawork Add unit tests for UserService
```

**What it does**:
- Analyzes task complexity
- Dispatches appropriate agents
- Executes with maximum efficiency
- Reports progress in real-time

---

### /run-workflow

**Purpose**: Run a predefined workflow

**Usage**:
```
/run-workflow <workflow-name>
```

**Available workflows**:
- `full-review` - Complete code review
- `deploy` - Deployment workflow
- `test-all` - Run all tests

---

### /enable-coordination

**Purpose**: Enable multi-agent coordination

**Usage**:
```
/enable-coordination
```

**What it does**:
- Enables agent coordination mode
- Allows multiple agents to work together
- Improves complex task handling

---

### /disable-coordination

**Purpose**: Disable multi-agent coordination

**Usage**:
```
/disable-coordination
```

**What it does**:
- Disables agent coordination mode
- Returns to single-agent mode
- Useful for simple tasks

---

## Skills

### Core Skills

| Skill | Purpose | Auto-triggered |
|-------|---------|----------------|
| project-memory-skill | Three-dimensional memory management | Yes |
| boulder-tracking-skill | Cross-session progress tracking | Yes |
| category-system-skill | Semantic task classification | Yes |

### Development Skills

| Skill | Purpose | Auto-triggered |
|-------|---------|----------------|
| inquiry-skill | 7-layer requirements inquiry | On init |
| tdd-workflow-skill | Test-driven development workflow | On code tasks |
| code-review-skill | Code quality review | On review |
| git-commit-skill | Git commit standardization | On commit |

### Tool Skills

| Skill | Purpose | Auto-triggered |
|-------|---------|----------------|
| multi-model-skill | Multi-model support | Yes |
| lsp-ast-skill | LSP/AST code analysis | On code tasks |
| project-detector-skill | Project type detection | On init |
| background-agents-skill | Parallel agent execution | On complex tasks |
| skill-integration-skill | Skill integration management | Manual |

---

## Workflows

### New Project Workflow

```
1. Trigger: 启动QuickAgent
   ↓
2. yinglong-init starts
   ↓
3. Project type detection
   ↓
4. Configuration check
   ↓
5. First-time setup (if needed)
   ↓
6. 7-layer requirements inquiry
   ↓
7. Tech stack recommendation
   ↓
8. Task breakdown
   ↓
9. Start execution
```

### Daily Development Workflow

```
1. Describe task to AI
   ↓
2. fenghou-orchestrate classifies task
   ↓
3. Appropriate agent is dispatched
   ↓
4. Task is executed
   ↓
5. Quality checks (review, test)
   ↓
6. Git commit
   ↓
7. Memory is updated
```

### Debugging Workflow

```
1. Report issue: @kuafu-debug <issue>
   ↓
2. kuafu-debug analyzes issue
   ↓
3. Root cause identified
   ↓
4. Fix is implemented
   ↓
5. Tests verify fix
   ↓
6. Code is reviewed
   ↓
7. Changes are committed
```

---

## Best Practices

### 1. Use Trigger Words Consistently

Always use `启动QuickAgent` for initialization. This ensures consistent behavior.

### 2. Complete Requirements Inquiry

Don't skip the 7-layer requirements inquiry. Answer each question thoroughly:
- L1: Business essence
- L2: User profile
- L3: Core flow
- L4: Feature list
- L5: Data model
- L6: Tech stack
- L7: Delivery standards

### 3. Leverage Agent Specialization

Use specific agents for specific tasks:
- `@jianming-review` for code review
- `@lishou-test` for testing
- `@mengzhang-security` for security
- `@kuafu-debug` for debugging

### 4. Use Cross-Session Recovery

When starting a new session:
```
/start-work
```

This restores your context and progress.

### 5. Commit Frequently

Let git-commit-skill handle commits:
- Standardized commit messages
- Pre-commit checks
- Documentation updates

### 6. Keep Memory Updated

MEMORY.md is your project's brain. Keep it updated:
- Record important decisions
- Document lessons learned
- Track current state

### 7. Use /ultrawork for Complex Tasks

For complex, multi-step tasks:
```
/ultrawork Implement complete user authentication system with OAuth2
```

---

## FAQ

### Q: How do I start a new project?

**A**: Simply use the trigger word:
```
启动QuickAgent
```
The system will guide you through the entire process.

### Q: How do I continue work after closing the session?

**A**: Use the recovery command:
```
/start-work
```

### Q: How do I call a specific agent?

**A**: Use @mention:
```
@jianming-review Please review this code
```

### Q: How do I change my model configuration?

**A**: Edit `.opencode/config/models.json` or run:
```
@huodi-skill Update model configuration
```

### Q: What if I don't have a Z.ai subscription?

**A**: You can configure other models in `models.json`. QuickAgents supports:
- Claude models
- GPT models
- Gemini models
- Local models

### Q: How do I add a new language for LSP?

**A**: Edit `.opencode/config/lsp-config.json`:
```json
{
  "languages": ["typescript", "python"],
  "servers": {
    "python": {
      "command": "pyright-langserver",
      "args": ["--stdio"]
    }
  }
}
```

### Q: How do I create a custom skill?

**A**: Use the skill management agent:
```
@huodi-skill Create a new skill for code formatting
```

### Q: What's the difference between /ultrawork and normal tasks?

**A**: `/ultrawork` is optimized for:
- Complex, multi-step tasks
- Tasks requiring multiple agents
- Tasks needing parallel execution

Normal tasks are handled by direct conversation.

### Q: How do I check my progress?

**A**: View the progress file:
```bash
cat .quickagents/boulder.json
```

Or ask the AI:
```
What's my current progress?
```

### Q: How do I reset QuickAgents?

**A**: Remove the configuration and reinitialize:
```bash
rm -rf .opencode
rm -rf .quickagents
rm AGENTS.md
启动QuickAgent
```

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────┐
│                    QuickAgents Quick Reference                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  TRIGGER WORDS                                                   │
│  ─────────────────────────────────────────────────────────────  │
│  启动QuickAgent  启动QuickAgents  启动QA  Start QA               │
│                                                                  │
│  COMMANDS                                                        │
│  ─────────────────────────────────────────────────────────────  │
│  /start-work      - Cross-session recovery                      │
│  /ultrawork       - Ultra-efficient execution                    │
│  /run-workflow    - Run predefined workflow                      │
│  /enable-coord    - Enable agent coordination                    │
│  /disable-coord   - Disable agent coordination                   │
│                                                                  │
│  COMMON AGENTS                                                   │
│  ─────────────────────────────────────────────────────────────  │
│  @jianming-review  - Code review                                │
│  @lishou-test      - Test execution                             │
│  @kuafu-debug      - Debugging                                  │
│  @cangjie-doc      - Documentation                              │
│                                                                  │
│  KEY FILES                                                       │
│  ─────────────────────────────────────────────────────────────  │
│  AGENTS.md                    - Development spec                 │
│  .opencode/config/models.json - Model configuration             │
│  Docs/MEMORY.md               - Project memory                  │
│  .quickagents/boulder.json    - Progress tracking               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

*Version: 2.1.0 | Last Updated: 2026-03-27*
