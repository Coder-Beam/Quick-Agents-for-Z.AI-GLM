# OpenCode Plugins Directory

This directory contains plugins for OpenCode.

## QuickAgents Unified Plugin

**Package Name**: `@coder-beam/quickagents`

**Version**: 2.1.0

### Features

| Module | Function | Token Savings |
|--------|----------|---------------|
| FileManager Cache | File hash detection | 60-100% |
| LoopDetector | Loop detection | 100% |
| Reminder | Event-driven reminders | Indirect |
| LocalExecutor | Local command execution | 100% |
| SkillEvolution | Skills self-evolution | 0 |
| FeedbackCollector | Experience collection | 0 |

### Installation

1. **Automatic** (via AGENTS.md startup flow)
   - Plugin is installed automatically when "启动QuickAgents" is triggered

2. **Manual**
   ```bash
   # Ensure quickagents is installed
   pip install quickagents
   
   # Plugin file is already in .opencode/plugins/quickagents.ts
   # OpenCode loads plugins automatically
   ```

### Configuration

In `opencode.json`:

```json
{
  "plugin": ["@coder-beam/quickagents"]
}
```

### Verification

Run the verification script:

```bash
python scripts/verify_plugin.py
```

### LocalExecutor Commands

The plugin intercepts these commands and executes them locally:

| Command | Description |
|---------|-------------|
| `qa memory get/set/search` | Memory operations |
| `qa knowledge search/trace` | Knowledge graph queries |
| `qa stats` | Statistics |
| `qa progress` | Progress tracking |
| `grep` tool | Content search (local ripgrep) |
| `glob` tool | File search (local traversal) |

### Token Savings Estimate

| Scenario | Savings |
|----------|---------|
| File-intensive | 60-80% |
| Search-intensive | 80-95% |
| Memory/graph-intensive | 90-100% |
| Mixed | 50-70% |

### Files

```
.opencode/plugins/
├── package.json        # Plugin metadata
├── quickagents.ts      # Main plugin code
└── README.md           # This file
```

### Links

- [QuickAgents Repository](https://github.com/Coder-Beam/QuickAgents)
- [Plugin Architecture](../../Docs/plugins/PLUGIN_ARCHITECTURE.md)
