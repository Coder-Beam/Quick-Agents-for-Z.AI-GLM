---
name: git-commit-skill
description: |
  Enforce standardized Git commit practices with conventional commit format.
  Includes pre-commit checks (tests, lint, typecheck), commit message validation,
  and automatic documentation updates.
license: MIT
allowed-tools:
  - read
  - write
  - edit
  - bash
metadata:
  category: version-control
  priority: critical
  version: 1.0.0
---

# Git Commit Skill

## Overview

Enforce standardized Git commit workflow ensuring code quality and traceability.
Every commit must pass pre-commit checks and follow conventional commit format.

## When to Use This Skill

Use this skill when:
- Completing a task or feature
- Before any git commit
- User requests commit assistance
- After fixing a bug
- After refactoring code
- Creating a release

## Commit Workflow

### Complete Commit Process

```
┌─────────────────────────────────────────────────────────────┐
│                    Git Commit Workflow                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. PRE-COMMIT CHECKS                                        │
│     ├─ Run all tests                                         │
│     ├─ Run lint check                                        │
│     ├─ Run typecheck                                         │
│     ├─ Check test coverage                                   │
│     └─ All must PASS before proceeding                       │
│                                                              │
│  2. DOCUMENTATION UPDATE                                     │
│     ├─ Update Docs/MEMORY.md                                 │
│     ├─ Update Docs/TASKS.md                                  │
│     ├─ Update other relevant docs                            │
│     └─ Sync to .opencode/memory/                             │
│                                                              │
│  3. STAGE CHANGES                                            │
│     ├─ Review git status                                     │
│     ├─ Review git diff                                       │
│     ├─ Stage appropriate files                               │
│     └─ Exclude sensitive files                               │
│                                                              │
│  4. CREATE COMMIT                                            │
│     ├─ Generate commit message                               │
│     ├─ Follow conventional format                            │
│     └─ Reference related task/issue                          │
│                                                              │
│  5. POST-COMMIT                                              │
│     ├─ Verify commit success                                 │
│     ├─ Update Experiential Memory                            │
│     ├─ Generate cross-session handoff                        │
│     └─ Push if requested                                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Pre-Commit Checks (MANDATORY)

### Check Sequence

```bash
# 1. Run all tests
npm test
# Must pass: 100%

# 2. Run lint
npm run lint
# Must pass: No errors

# 3. Run typecheck
npm run typecheck
# Must pass: No errors

# 4. Check coverage (if configured)
npm run test:coverage
# Must meet threshold: Core 100%, Non-core 80%
```

### Failure Handling

```
If ANY check fails:
1. STOP - Do not commit
2. FIX the issue
3. RE-RUN all checks
4. Only proceed when ALL pass
```

## Conventional Commit Format

### Message Structure

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

### Types

| Type | Description | Example |
|------|-------------|---------|
| `feat` | New feature | `feat(auth): add OAuth login` |
| `fix` | Bug fix | `fix(api): handle null response` |
| `docs` | Documentation only | `docs(readme): update install steps` |
| `style` | Code style (no logic change) | `style: format with prettier` |
| `refactor` | Code refactoring | `refactor(utils): extract helper` |
| `perf` | Performance improvement | `perf(db): optimize query` |
| `test` | Adding/updating tests | `test(auth): add login tests` |
| `chore` | Build/tooling changes | `chore: update dependencies` |
| `ci` | CI configuration | `ci: add GitHub Actions` |

### Scopes

Use module/feature name as scope:
- `feat(auth): ...` - Authentication module
- `fix(api): ...` - API module
- `docs(readme): ...` - README file
- `chore(deps): ...` - Dependencies

### Subject Rules

1. Use imperative mood: "add" not "added" or "adds"
2. Don't capitalize first letter
3. No period at end
4. Max 50 characters
5. Be specific and descriptive

### Examples

```bash
# Good
feat(skills): add project-memory-skill with 3D memory system
fix(agents): resolve template rendering issue
docs(agents): update project-initializer documentation
refactor(utils): extract common validation logic
test(tdd): add RED-GREEN-REFACTOR cycle tests

# Bad
Added new feature
fix bug
Update stuff
WIP
```

## Commit Message Templates

### Feature Commit

```
feat(<scope>): <brief description>

- Add <specific feature 1>
- Implement <specific feature 2>
- Include <related changes>

Closes #<issue-number>
```

### Bug Fix Commit

```
fix(<scope>): <brief description of bug>

- Root cause: <explanation>
- Fix: <how it was fixed>
- Test: <test added to prevent regression>

Fixes #<issue-number>
```

### Refactor Commit

```
refactor(<scope>): <what was refactored>

- Extract <method/class>
- Simplify <logic>
- Remove <dead code>

No behavior changes
```

### Documentation Commit

```
docs(<scope>): <what was documented>

- Add <section>
- Update <outdated info>
- Fix <typos>

Related to #<issue-number>
```

## Staging Strategy

### Review Before Staging

```bash
# Check what changed
git status

# Review changes
git diff

# Review staged changes
git diff --staged
```

### What to Stage

```
✅ ALWAYS STAGE:
- Source code changes
- Test files
- Documentation updates
- Configuration changes
- Type definitions

❌ NEVER STAGE:
- .env files (secrets)
- node_modules/
- dist/ build/
- *.log files
- IDE settings (.idea/, .vscode/)
- Credentials and keys
```

### Staging Commands

```bash
# Stage specific files
git add src/feature.ts src/feature.test.ts

# Stage all changes in directory
git add src/auth/

# Stage all changes (be careful)
git add .

# Interactive staging
git add -p
```

## Documentation Sync

### Files to Update Before Commit

```
1. Docs/MEMORY.md
   - Update Working Memory (current state)
   - Update Experiential Memory (operation history)
   - Add any new decisions to Factual Memory

2. Docs/TASKS.md
   - Mark completed tasks
   - Update task status
   - Add new tasks if discovered

3. Docs/DESIGN.md (if architecture changed)
   - Update architecture section
   - Document new components

4. Docs/DECISIONS.md (if decision made)
   - Add decision entry
   - Document rationale

5. .opencode/memory/
   - Sync all updated docs
```

### Sync Command

```bash
# Sync Docs to .opencode/memory
cp -r Docs/* .opencode/memory/

# Or use git hook (recommended)
# .git/hooks/pre-commit
```

## Commit Verification

### Post-Commit Checks

```bash
# Verify commit was created
git log -1

# Verify commit hash
git rev-parse HEAD

# Verify commit message
git log -1 --format="%s"

# Verify files in commit
git show --stat
```

### Expected Output

```
commit abc123def456...
Author: Your Name <email@example.com>
Date:   Mon Mar 25 10:00:00 2026 +0800

    feat(skills): add project-memory-skill with 3D memory system
    
    - Implement Factual/Experiential/Working memory types
    - Add memory operations (create/update/retrieve/evolve)
    - Include cross-session handoff prompt generation

 Docs/MEMORY.md                              |  45 ++++-
 .opencode/skills/project-memory-skill/SKILL.md | 256 +++++++++++++++
 2 files changed, 301 insertions(+)
```

## Post-Commit Actions

### Update Memory

```markdown
### 2.1 Operation History

| Time | Operation | Result | Notes |
|------|-----------|--------|-------|
| 2026-03-25 | Commit abc123 | Success | feat(skills): add project-memory-skill |
```

### Generate Handoff Prompt

```text
📍 Cross-Session Handoff Prompt

## Current Progress
- Completed: project-memory-skill creation
- Progress: 40%
- Latest Commit: abc123 - feat(skills): add project-memory-skill

## Context Summary
- Project: QuickAgents
- Tech Stack: TypeScript + OpenCode
- Current Stage: Phase 2 - Core Development

## Key Decisions
- D006: Memory uses file storage

## Next Task
- Task ID: T003
- Name: Create tdd-workflow-skill
- Estimate: 30 minutes
```

## Commit Frequency

### When to Commit

```
✅ COMMIT after:
- Completing a feature
- Fixing a bug
- Refactoring code
- Updating documentation
- Passing all tests
- Making a decision

❌ DON'T COMMIT:
- In the middle of a task
- With failing tests
- With lint errors
- Without documentation update
- Large unrelated changes together
```

### Atomic Commits

```
GOOD (atomic):
- feat(auth): add login validation
- test(auth): add login validation tests
- docs(auth): document login flow

BAD (not atomic):
- feat: add auth, fix bugs, update docs, refactor utils
```

## Branch Strategy

### Branch Naming

```
feature/<ticket>-<description>   # New feature
fix/<ticket>-<description>       # Bug fix
refactor/<description>           # Refactoring
docs/<description>               # Documentation
```

### Examples

```bash
feature/AUTH-123-oauth-login
fix/API-456-null-response
refactor/extract-validation-utils
docs/update-readme
```

## Common Commands Reference

```bash
# Check status
git status

# View diff
git diff

# Stage changes
git add <files>

# Commit
git commit -m "type(scope): subject"

# View log
git log --oneline -10

# Amend last commit (use carefully)
git commit --amend

# Push
git push origin <branch>

# Create branch
git checkout -b feature/new-feature
```

## Integration with QuickAgents

### Before Commit
```markdown
1. Run pre-commit checks (tests, lint, typecheck)
2. Update Docs/MEMORY.md
3. Update Docs/TASKS.md
4. Sync to .opencode/memory/
```

### During Commit
```markdown
1. Review git status and diff
2. Stage appropriate files
3. Generate conventional commit message
4. Execute commit
```

### After Commit
```markdown
1. Verify commit success
2. Update Experiential Memory
3. Generate cross-session handoff
4. Update TASKS.md progress
```

## Best Practices

1. **Commit often, push when ready**
2. **One logical change per commit**
3. **Write clear, descriptive messages**
4. **Always run tests before commit**
5. **Update documentation with code**
6. **Reference issues/tasks in commits**
7. **Never commit secrets**
8. **Review your diff before staging**
9. **Use branches for features**
10. **Keep commits atomic**

## Resources

- Template: `./assets/commit-template.md`
- Examples: `./references/example-commits.md`
- Conventional Commits: https://www.conventionalcommits.org/
