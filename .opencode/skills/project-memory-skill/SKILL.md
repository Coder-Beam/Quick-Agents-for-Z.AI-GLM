---
name: project-memory-skill
description: |
  Manage the three-dimensional memory system (Factual/Experiential/Working)
  for projects. Based on the paper "Memory in the Age of AI Agents". Supports
  creation, update, retrieval, and evolution of project memories across sessions.
license: MIT
allowed-tools:
  - read
  - write
  - edit
  - grep
  - glob
metadata:
  category: memory
  priority: critical
  version: 2.1.0
---

# Project Memory Skill

## Overview

Implement a three-dimensional memory system that maintains project context across
AI sessions. Combines Factual (static facts), Experiential (dynamic experience),
and Working (active state) memories for comprehensive project knowledge management.

## When to Use This Skill

Use this skill when:
- Starting a new project (create MEMORY.md)
- Completing a task (update Working/Experiential Memory)
- Making a decision (record to Factual Memory)
- Before Git commit (auto-record commit info)
- Starting a new session (restore context from MEMORY.md)
- User requests memory search or update
- Cross-session handoff is needed

## The Three Memory Dimensions

### Factual Memory

**Purpose**: Record static, unchanging project facts

| Category | Content | Examples |
|----------|---------|----------|
| Project Meta | Name, path, tech stack, dependencies | `name: QuickAgents`, `tech: TypeScript` |
| Technical Decisions | Architecture, API design, database schema | D001: Use TypeScript for type safety |
| Business Rules | Logic, calculations, validations | Rule1: All requirements must be clarified |
| Constraints | Technical, business, time, resources | Node.js >= 18, 13-week timeline |

**Format**:
```markdown
### 1.2 Technical Decisions

| Decision ID | Content | Date | Rationale |
|-------------|---------|------|-----------|
| D001 | Use TypeScript | 2026-03-25 | Type safety, OpenCode compatibility |
```

### Experiential Memory

**Purpose**: Record dynamic, evolving project experiences

| Category | Content | Examples |
|----------|---------|----------|
| Operation History | Completed tasks, changes, operations | 2026-03-25: Created inquiry-skill |
| Lessons Learned | Pitfalls, best practices, takeaways | Avoid over-engineering |
| User Feedback | Opinions, adjustments, acceptance | User prefers quick mode |
| Iteration Records | Version changes, feature evolution | v1.0 → v8.0: Added 9 agents |

**Format**:
```markdown
### 2.2 Lessons Learned

#### Pitfalls
- **Over-engineering risk**: Initial plan was too complex
- **Solution**: User corrected, focus on Agent+Skill essence

#### Best Practices
1. **RSI Philosophy**: Minimal human intervention, self-improvement
2. **Plugin Ecosystem**: Leverage existing OpenCode plugins
```

### Working Memory

**Purpose**: Track current active state and pending items

| Category | Content | Examples |
|----------|---------|----------|
| Current State | Active task, progress %, blockers | Task: Create skills, Progress: 35% |
| Active Context | Related files, dependencies, preconditions | AGENTS.md, Docs/MEMORY.md |
| Temporary Variables | Pending items, temp decisions, cache | 5 skills remaining |
| Pending Decisions | Questions needing user confirmation | D005: Support quick mode? |

**Format**:
```markdown
### 3.1 Current State

| Attribute | Value |
|-----------|-------|
| Current Task | Skills creation |
| Progress | 35% |
| Blockers | None |
| Stage | Phase 2: Core Development |
```

## Memory File Structure

### Standard Template

```yaml
---
# YAML Front Matter - Metadata
memory_type: project | feature | module
created_at: 2026-03-22T10:00:00Z
updated_at: 2026-03-25T15:30:00Z
version: 2.0.0
tags: [project, initialization, agent]
related_files: [AGENTS.md, TASKS.md, DESIGN.md]
---

# Project Memory (MEMORY.md)

> Three-dimensional memory system based on "Memory in the Age of AI Agents"

---

## One, Factual Memory

### 1.1 Project Meta Information
...

### 1.2 Technical Decisions
...

### 1.3 Business Rules
...

### 1.4 Constraints
...

---

## Two, Experiential Memory

### 2.1 Operation History
...

### 2.2 Lessons Learned
...

### 2.3 User Feedback
...

### 2.4 Iteration Records
...

---

## Three, Working Memory

### 3.1 Current State
...

### 3.2 Active Context
...

### 3.3 Temporary Variables
...

### 3.4 Pending Decisions
...

---

## Four, Memory Index

### 4.1 By Tag
...

### 4.2 By Time
...

---

*Last Updated: 2026-03-25*
```

## Memory Operations

### Create Memory

When creating a new memory file:

```
1. Determine memory level (project/feature/module)
2. Create MEMORY.md using standard template
3. Fill YAML Front Matter metadata
4. Initialize all three memory sections
5. Add initial tags and related files
```

**Example**:
```markdown
# For new feature
memory_type: feature
created_at: 2026-03-25T10:00:00Z
tags: [feature, authentication]
```

### Update Memory

When updating memory:

```
1. Identify update type (Factual/Experiential/Working)
2. Append new content (never delete)
3. Update updated_at timestamp
4. Add relevant tags
5. Update related_files if new files created
```

**Update Triggers**:
| Trigger | Memory Type | Action |
|---------|-------------|--------|
| Task complete | Experiential + Working | Record operation, update state |
| Decision made | Factual | Add to decisions table |
| Git commit | Experiential | Record commit info |
| New session | Working | Clear temp variables |
| User feedback | Experiential | Add to feedback section |

### Retrieve Memory

When searching memories:

```
1. Keyword matching in content
2. Tag filtering
3. Time range filtering
4. Related file lookup
5. Sort by relevance
```

**Search Patterns**:
```bash
# By tag
grep "#initialization" Docs/MEMORY.md

# By time
grep "2026-03-25" Docs/MEMORY.md

# By decision ID
grep "D001" Docs/MEMORY.md
```

### Evolve Memory

Periodic memory consolidation:

```
1. Identify duplicate entries
2. Merge similar content
3. Archive old working states
4. Preserve complete history
5. NEVER delete any memory
```

**Evolution Rules**:
- Working Memory: Reset at session start, archive to Experiential
- Experiential Memory: Merge duplicates, keep timeline
- Factual Memory: Only add, never modify

## Memory Hierarchy

### Three-Level Structure

```
Project Level (Docs/MEMORY.md)
    ├── Feature Level (Docs/features/{name}/MEMORY.md)
    │       └── Module Level (Docs/modules/{name}/MEMORY.md)
    └── Module Level (Docs/modules/{name}/MEMORY.md)
```

### Sync Rules

1. **Bottom-up**: Module → Feature → Project (aggregate summaries)
2. **Top-down**: Project decisions propagate to all levels
3. **Cross-level**: Related files reference each level

## Integration with QuickAgents

### Before Task
```markdown
1. Read Docs/MEMORY.md to restore context
2. Check Working Memory for current state
3. Review pending decisions
4. Identify blockers
```

### During Task
```markdown
1. Update Working Memory with progress
2. Record temporary decisions
3. Track active context (files being modified)
4. Log any new constraints discovered
```

### After Task
```markdown
1. Update Experiential Memory (operation history)
2. Record lessons learned
3. Update Working Memory (next task, cleared blockers)
4. Sync across levels if needed
```

### Git Commit Hook
```markdown
1. Record commit hash to Experiential Memory
2. Update Working Memory progress
3. Add commit message to operation history
4. Generate cross-session handoff prompt
```

## Cross-Session Handoff

### Generate Handoff Prompt

After each Git commit, auto-generate:

```text
📍 Cross-Session Handoff Prompt

## Current Progress
- Completed: [task name]
- Progress: [X%]
- Latest Commit: [hash] - [message]

## Context Summary
- Project: [name]
- Tech Stack: [stack]
- Current Stage: [stage]

## Key Decisions
- [D001]: [summary]
- [D002]: [summary]

## Risk Alerts
- [Risk]: [status]

## Dependencies
- Prerequisites: [status]
- Next Tasks: [list]

## Next Task
- Task ID: [T-XXX]
- Name: [description]
- Estimate: [X hours]

## Memory Files
- Project: Docs/MEMORY.md
- Tasks: Docs/TASKS.md
- Design: Docs/DESIGN.md

---
Copy and paste in new session to continue
```

## Best Practices

1. **Never Delete**: All memories are permanent, only merge/consolidate
2. **Real-time Updates**: Working Memory must be current
3. **Cross-level Sync**: Feature/module changes update project memory
4. **Git Integration**: Every commit triggers memory update
5. **Timestamp Everything**: All entries need timestamps
6. **Tag Generously**: Tags enable efficient retrieval
7. **Link Files**: Related files create knowledge graph

## Memory File Locations

| Level | Path |
|-------|------|
| Project | `Docs/MEMORY.md` |
| Feature | `Docs/features/{name}/MEMORY.md` |
| Module | `Docs/modules/{name}/MEMORY.md` |
| OpenCode | `.opencode/memory/MEMORY.md` (sync with Docs/) |

## Resources

- Template: `./assets/memory-template.md`
- Examples: `./references/example-memories.md`
- Evolution Log: `./EVOLUTION.md`
