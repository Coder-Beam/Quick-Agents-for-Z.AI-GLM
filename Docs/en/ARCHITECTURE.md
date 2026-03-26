# QuickAgents System Architecture

> This document provides a detailed introduction to QuickAgents' system architecture, design philosophy, and core components.

---

## Table of Contents

- [Overview](#overview)
- [Design Philosophy](#design-philosophy)
- [Core Components](#core-components)
- [Directory Structure](#directory-structure)
- [Configuration System](#configuration-system)
- [Data Flow](#data-flow)
- [Agent System](#agent-system)
- [Skill System](#skill-system)
- [Memory System](#memory-system)

---

## Overview

QuickAgents is a complete AI agent project initialization system built on the OpenCode platform, providing:

- **17 Professional Agents**: Covering the entire process of project initialization, development, testing, and deployment
- **12 Specialized Skills**: Providing core capabilities such as memory management, progress tracking, and code analysis
- **6 Core Commands**: Supporting cross-session recovery, ultra-efficient execution, and more
- **Three-Dimensional Memory System**: Factual/Experiential/Working memory architecture based on academic papers

---

## Design Philosophy

### 1. Zero Assumption Principle

Never assume or guess any requirement details, business scenarios, constraints, or success criteria that have not been explicitly confirmed by the user.

### 2. Essence-First Principle

Always ask "why" first, then discuss "what", and finally talk about "how".

### 3. Full-Chain Risk Front-Loading

Identify technical risks, business risks, compliance risks, operational risks, and cost risks immediately for any requirements and solutions.

### 4. Never Decide for Users

Only provide professional technical solutions, risk assessments, and alternatives. Never make any business decisions for users.

### 5. Three-Dimensional Memory Driven

Designed based on the paper "Memory in the Age of AI Agents", supporting cross-session state recovery and knowledge accumulation.

---

## Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        QuickAgents System                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Agents    │  │   Skills    │  │  Commands   │              │
│  │   17 agents │  │   12 skills │  │   6 commands│              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                      │
│         └────────────────┼────────────────┘                      │
│                          │                                       │
│                          ▼                                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Orchestration Layer                     │  │
│  │                  (fenghou-orchestrate)                     │  │
│  └───────────────────────────────────────────────────────────┘  │
│                          │                                       │
│                          ▼                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Memory    │  │   Config    │  │   Hooks     │              │
│  │   System    │  │   System    │  │   System    │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
QuickAgents/
├── AGENTS.md                    # Development specification (core file)
│
├── .opencode/                   # OpenCode configuration directory
│   │
│   ├── agents/                  # Agent configurations (17)
│   │   ├── README.md
│   │   ├── yinglong-init.md     # Project initialization
│   │   ├── boyi-consult.md      # Requirements analysis
│   │   ├── chisongzi-advise.md  # Tech recommendation
│   │   ├── cangjie-doc.md       # Documentation management
│   │   ├── huodi-skill.md       # Skill management
│   │   ├── fenghou-orchestrate.md # Main orchestrator
│   │   ├── fenghou-plan.md      # Planner
│   │   ├── jianming-review.md   # Code review
│   │   ├── lishou-test.md       # Test execution
│   │   ├── mengzhang-security.md # Security audit
│   │   ├── hengge-perf.md       # Performance analysis
│   │   ├── kuafu-debug.md       # Debugging agent
│   │   ├── gonggu-refactor.md   # Refactoring agent
│   │   ├── huodi-deps.md        # Dependency management
│   │   └── hengge-cicd.md       # CI/CD management
│   │
│   ├── skills/                  # Skill configurations (12)
│   │   ├── EVOLUTION.md         # Skill evolution records
│   │   ├── registry.json        # Skill registry
│   │   ├── project-memory-skill/
│   │   ├── boulder-tracking-skill/
│   │   ├── category-system-skill/
│   │   ├── inquiry-skill/
│   │   ├── tdd-workflow-skill/
│   │   ├── code-review-skill/
│   │   ├── git-commit-skill/
│   │   ├── multi-model-skill/
│   │   ├── lsp-ast-skill/
│   │   ├── project-detector-skill/
│   │   ├── background-agents-skill/
│   │   └── skill-integration-skill/
│   │
│   ├── commands/                # Command configurations (6)
│   │   ├── README.md
│   │   ├── start-work.md
│   │   ├── ultrawork.md
│   │   ├── run-workflow.md
│   │   ├── enable-coordination.md
│   │   └── disable-coordination.md
│   │
│   ├── hooks/                   # Hook configurations
│   │   ├── README.md
│   │   └── todo-continuation-enforcer.md
│   │
│   ├── config/                  # Configuration files
│   │   ├── quickagents.json     # QuickAgents configuration
│   │   ├── categories.json      # Task classification config
│   │   └── lsp-config.json      # LSP configuration
│   │
│   ├── memory/                  # Project memory (synced with Docs/)
│   │   ├── MEMORY.md
│   │   ├── TASKS.md
│   │   ├── DESIGN.md
│   │   ├── INDEX.md
│   │   └── DECISIONS.md
│   │
│   └── plugins/                 # Plugin directory
│       └── README.md
│
├── Docs/                        # Project documentation
│   ├── README.md                # Documentation navigation
│   ├── AGENT_GUIDE.md           # Agent usage guide
│   ├── USER_GUIDE.md            # User guide
│   ├── ARCHITECTURE.md          # Architecture docs
│   ├── API_REFERENCE.md         # API reference
│   ├── EXAMPLES.md              # Usage examples
│   ├── MEMORY.md                # Project memory
│   ├── TASKS.md                 # Task management
│   ├── DESIGN.md                # Design documents
│   ├── INDEX.md                 # Knowledge graph
│   ├── DECISIONS.md             # Decision log
│   ├── guide/
│   │   └── installation.md      # Installation guide
│   └── en/                      # English documents
│       ├── AGENT_GUIDE.md
│       ├── USER_GUIDE.md
│       ├── ARCHITECTURE.md
│       └── guide/
│           └── installation.md
│
├── .quickagents/                # QuickAgents data
│   └── boulder.json             # Progress tracking data
│
└── packages/                    # NPM packages
    └── quickagents-cli/         # CLI tool
```

---

## Configuration System

### quickagents.json

Main configuration file controlling QuickAgents' core behavior:

```json
{
  "version": "2.0.1",
  "triggerWords": [
    "启动QuickAgent",
    "启动QuickAgents",
    "启动QA",
    "Start QA"
  ],
  "agents": {
    "enabled": true,
    "autoCreate": true
  },
  "skills": {
    "enabled": true,
    "autoEvolve": true
  },
  "memory": {
    "type": "three-dimensional",
    "sync": true
  }
}
```

### categories.json

Task classification configuration for intelligent model selection:

```json
{
  "version": "2.0.1",
  "categories": {
    "quick": {
      "description": "Quick tasks",
      "model": "flash",
      "maxTokens": 4000
    },
    "planning": {
      "description": "Planning tasks",
      "model": "pro",
      "maxTokens": 16000
    },
    "coding": {
      "description": "Coding tasks",
      "model": "pro",
      "maxTokens": 8000
    }
  }
}
```

### lsp-config.json

LSP server configuration supporting multiple languages:

```json
{
  "version": "2.0.1",
  "languages": ["typescript", "python", "rust"],
  "ast-grep": true,
  "servers": {
    "typescript": {
      "command": "typescript-language-server",
      "args": ["--stdio"]
    }
  }
}
```

---

## Data Flow

### Initialization Flow

```
User Trigger → yinglong-init → Environment Check
                    ↓
              Read Config → Check First Use
                    ↓
              First-time Setup Wizard (models.json, lsp-config.json)
                    ↓
              7-Layer Requirements Inquiry (inquiry-skill)
                    ↓
              Create Directory Structure → Initialize Docs
                    ↓
              Create Standard Agents (programming projects)
                    ↓
              Start First Task
```

### Task Execution Flow

```
User Task → fenghou-orchestrate → Classification (category-system-skill)
                    ↓
              Model Selection (multi-model-skill)
                    ↓
              Dispatch Agent → Execute Task
                    ↓
              Record Memory (project-memory-skill)
                    ↓
              Update Progress (boulder-tracking-skill)
                    ↓
              Git Commit (git-commit-skill)
```

### Cross-Session Recovery Flow

```
/start-work → Read MEMORY.md → Read boulder.json
                    ↓
              Restore Context → Display Progress
                    ↓
              Continue Execution → Update State
```

---

## Agent System

### Agent Categories

| Category | Agents | Responsibilities |
|----------|--------|------------------|
| **Core** | yinglong-init | Project initialization |
| | boyi-consult | Requirements analysis & consulting |
| | chisongzi-advise | Tech stack recommendation |
| | cangjie-doc | Documentation management |
| | huodi-skill | Skill management |
| | fenghou-orchestrate | Main orchestrator |
| **Quality** | jianming-review | Code review |
| | lishou-test | Test execution |
| | mengzhang-security | Security audit |
| | hengge-perf | Performance analysis |
| **Tools** | kuafu-debug | Debugging agent |
| | gonggu-refactor | Refactoring agent |
| | huodi-deps | Dependency management |
| | hengge-cicd | CI/CD management |
| **Planning** | fenghou-plan | Planner |

### Agent Collaboration

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Request                             │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                  fenghou-orchestrate                            │
│                      (Main Orchestrator)                        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  Planning     │   │  Execution    │   │   Quality     │
│    Phase      │   │    Phase      │   │    Phase      │
├───────────────┤   ├───────────────┤   ├───────────────┤
│ fenghou-plan  │   │ gonggu-refactor│   │ jianming-review│
│ boyi-consult  │   │ huodi-deps    │   │ lishou-test   │
│               │   │ hengge-cicd   │   │ mengzhang-security│
└───────────────┘   └───────────────┘   │ hengge-perf   │
                                        └───────────────┘
```

---

## Skill System

### Skill Categories

| Category | Skill | Purpose |
|----------|-------|---------|
| **Core** | project-memory-skill | Three-dimensional memory management |
| | boulder-tracking-skill | Cross-session progress tracking |
| | category-system-skill | Semantic task classification |
| **Development** | inquiry-skill | 7-layer requirements inquiry |
| | tdd-workflow-skill | Test-driven development |
| | code-review-skill | Code quality review |
| | git-commit-skill | Git commit standardization |
| **Tools** | multi-model-skill | Multi-model support |
| | lsp-ast-skill | LSP/AST code analysis |
| | project-detector-skill | Project type detection |
| | background-agents-skill | Parallel agent execution |
| | skill-integration-skill | Skill integration management |

### Skill Evolution Mechanism

```
Task Complete → Analyze Usage → Identify Improvements
                      ↓
              Record Suggestions in MEMORY.md
                      ↓
              Every 10 tasks or weekly → Execute Optimization
                      ↓
              Comprehensive Evaluation (Stats + Feedback + Self-assessment)
                      ↓
              Update Skill → Record in EVOLUTION.md
```

---

## Memory System

### Three-Dimensional Memory Architecture

Based on the paper "Memory in the Age of AI Agents":

```
┌─────────────────────────────────────────────────────────────────┐
│                      Memory System                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Factual Memory  │  │Experiential Mem │  │ Working Memory  │  │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────────┤  │
│  │ • Project meta  │  │ • Operation     │  │ • Current task  │  │
│  │ • Tech decisions│  │   history       │  │ • Active context│  │
│  │ • Business rules│  │ • Lessons learned│  │ • Pending items │  │
│  │ • Constraints   │  │ • User feedback │  │ • Temp variables│  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                                  │
│  Formation ──────────► Retrieval ──────────► Evolution          │
│  (Trigger)             (Smart Search)       (Smart Integration)  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Memory Storage

Memory is stored in `MEMORY.md` file using a hybrid format:

```yaml
---
# YAML Front Matter - Metadata
memory_type: project | feature | module
created_at: 2026-03-26T10:00:00Z
updated_at: 2026-03-26T15:30:00Z
version: 2.0.1
tags: [tag1, tag2, tag3]
---

# Markdown Body - Content
```

---

## Extensibility

### Adding New Agents

1. Create `agent-name.md` in `.opencode/agents/`
2. Add YAML front matter configuration
3. Add index in `INDEX.md`

### Adding New Skills

1. Create `skill-name/` directory in `.opencode/skills/`
2. Create `SKILL.md` documentation
3. Register in `registry.json`

### Adding New Commands

1. Create `command-name.md` in `.opencode/commands/`
2. Define command behavior and parameters
3. Update documentation

---

*Version: 2.0.1 | Last Updated: 2026-03-26*
