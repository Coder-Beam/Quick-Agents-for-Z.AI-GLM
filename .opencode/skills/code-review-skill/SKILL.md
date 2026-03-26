---
name: code-review-skill
description: |
  Perform systematic code review focusing on correctness, maintainability,
  security, and performance. Based on superpowers two-phase review methodology
  (specification + quality review).
license: MIT
allowed-tools:
  - read
  - grep
  - glob
  - bash
metadata:
  category: quality
  priority: critical
  version: 1.0.0
---

# Code Review Skill

## Overview

Perform comprehensive code reviews to ensure code quality, correctness, and
maintainability. Uses a two-phase approach: specification review (does it work?)
followed by quality review (is it well-written?).

## When to Use This Skill

Use this skill when:
- Completing a feature implementation
- Before committing code
- After refactoring
- Reviewing pull requests
- User requests code review
- Identifying technical debt

## Two-Phase Review Methodology

### Phase 1: Specification Review

**Goal**: Verify code meets requirements and works correctly

```
1. Does the code do what it's supposed to do?
2. Are all requirements met?
3. Are edge cases handled?
4. Do tests cover the functionality?
5. Are there any bugs?
```

### Phase 2: Quality Review

**Goal**: Ensure code is maintainable and follows best practices

```
1. Is the code readable and understandable?
2. Does it follow project conventions?
3. Is it properly tested?
4. Are there security concerns?
5. Is it performant?
```

## Review Checklist

### 1. Correctness

| Check | Description | Severity |
|-------|-------------|----------|
| Requirements | Does code meet all requirements? | Critical |
| Logic | Is the logic correct? | Critical |
| Edge Cases | Are edge cases handled? | High |
| Error Handling | Are errors handled properly? | High |
| Type Safety | Are types correct? | High |

**Questions to Ask**:
- What does this code do?
- Does it match the specification?
- What happens with invalid input?
- What happens with null/undefined?
- What happens with empty collections?

### 2. Code Quality

| Check | Description | Severity |
|-------|-------------|----------|
| Readability | Is code easy to understand? | Medium |
| Naming | Are names clear and meaningful? | Medium |
| DRY | Is code duplication avoided? | Medium |
| Functions | Are functions focused and small? | Medium |
| Comments | Are comments helpful? | Low |

**Questions to Ask**:
- Can I understand this in 6 months?
- Do names reveal intent?
- Can this be simplified?
- Is there repeated code?
- Are comments explaining "why" not "what"?

### 3. Testing

| Check | Description | Severity |
|-------|-------------|----------|
| Coverage | Are all paths tested? | Critical |
| Unit Tests | Are unit tests present? | High |
| Edge Cases | Are edge cases tested? | High |
| Integration | Are integration tests needed? | Medium |
| Test Quality | Are tests meaningful? | Medium |

**Questions to Ask**:
- What tests exist for this code?
- Do tests cover edge cases?
- Are tests readable?
- Do tests actually verify behavior?
- What's not tested?

### 4. Security

| Check | Description | Severity |
|-------|-------------|----------|
| Input Validation | Is input validated? | Critical |
| Authentication | Are auth checks correct? | Critical |
| Authorization | Are permissions checked? | Critical |
| Data Exposure | Is sensitive data protected? | Critical |
| Injection | Is code injection prevented? | Critical |

**Questions to Ask**:
- Where does this data come from?
- Is user input sanitized?
- Are secrets exposed?
- Could this be exploited?
- What's the worst that could happen?

### 5. Performance

| Check | Description | Severity |
|-------|-------------|----------|
| Algorithm | Is algorithm efficient? | Medium |
| Memory | Is memory usage reasonable? | Medium |
| Database | Are queries optimized? | Medium |
| Caching | Can caching help? | Low |
| Lazy Loading | Can loading be deferred? | Low |

**Questions to Ask**:
- What's the time complexity?
- How much memory does this use?
- Are there N+1 queries?
- Can this be cached?
- Is this on the critical path?

### 6. Maintainability

| Check | Description | Severity |
|-------|-------------|----------|
| Modularity | Is code modular? | Medium |
| Dependencies | Are dependencies minimal? | Medium |
| Coupling | Is coupling loose? | Medium |
| Documentation | Is code documented? | Low |
| Tech Debt | Is debt documented? | Low |

**Questions to Ask**:
- How hard is this to change?
- What would break if I modify this?
- Are dependencies necessary?
- Is this over-engineered?

## Review Process

### Step 1: Understand Context

```
1. Read related task/issue
2. Check Docs/TASKS.md for requirements
3. Check Docs/DESIGN.md for architecture
4. Understand what was changed and why
```

### Step 2: Review Changes

```bash
# View what changed
git diff main...HEAD

# View changed files
git diff --name-only main...HEAD

# View specific file
git diff main...HEAD -- path/to/file.ts
```

### Step 3: Analyze Code

```
For each changed file:
1. Read the entire file (not just changes)
2. Identify the purpose of changes
3. Check against review checklist
4. Note issues found
```

### Step 4: Generate Report

```markdown
## Code Review Report

### Summary
[Brief overview of changes and overall assessment]

### Critical Issues 🔴
[Issues that must be fixed before merge]

### Warnings 🟡
[Issues that should be addressed but not blocking]

### Suggestions 🟢
[Improvement ideas, optional]

### Positive Notes ✅
[What's done well]

### Test Coverage
[Assessment of test coverage]

### Security Considerations
[Any security concerns]
```

## Issue Classification

### Severity Levels

| Level | Description | Action Required |
|-------|-------------|-----------------|
| 🔴 Critical | Bug, security issue, breaks functionality | MUST FIX before merge |
| 🟡 Warning | Code smell, maintainability issue | SHOULD FIX before merge |
| 🟢 Suggestion | Improvement opportunity | Consider for future |
| ✅ Positive | Good practice observed | None (acknowledge) |

### Issue Template

```markdown
**File**: `path/to/file.ts:123`
**Severity**: 🔴 Critical / 🟡 Warning / 🟢 Suggestion
**Category**: Correctness / Quality / Security / Performance / Testing

**Issue**:
[Description of the problem]

**Current Code**:
```typescript
// problematic code here
```

**Suggested Fix**:
```typescript
// improved code here
```

**Reason**:
[Why this is a problem and how the fix helps]
```

## Common Issues to Look For

### Correctness Issues

```typescript
// ❌ Missing null check
function getName(user: User) {
  return user.profile.name; // Crash if profile is null
}

// ✅ With null check
function getName(user: User) {
  return user.profile?.name ?? 'Unknown';
}

// ❌ Off-by-one error
for (let i = 0; i <= items.length; i++) { }

// ✅ Correct loop
for (let i = 0; i < items.length; i++) { }
```

### Quality Issues

```typescript
// ❌ Magic numbers
if (status === 1) { }

// ✅ Named constants
if (status === Status.ACTIVE) { }

// ❌ Long function
function processData(data: any) {
  // 100 lines of code...
}

// ✅ Smaller functions
function processData(data: any) {
  const validated = validateData(data);
  const transformed = transformData(validated);
  return saveData(transformed);
}
```

### Security Issues

```typescript
// ❌ SQL injection
const query = `SELECT * FROM users WHERE id = ${userId}`;

// ✅ Parameterized query
const query = 'SELECT * FROM users WHERE id = ?';
db.query(query, [userId]);

// ❌ Exposed secret
const apiKey = 'sk-1234567890';

// ✅ Environment variable
const apiKey = process.env.API_KEY;
```

### Performance Issues

```typescript
// ❌ N+1 query
for (const user of users) {
  const posts = await getPosts(user.id);
}

// ✅ Batch query
const posts = await getAllPosts(userIds);

// ❌ Synchronous in loop
for (const item of items) {
  await processItem(item);
}

// ✅ Parallel processing
await Promise.all(items.map(processItem));
```

## Review Commands

### Analyze Code

```bash
# Find TODO/FIXME comments
grep -rn "TODO\|FIXME" src/

# Find console.logs
grep -rn "console\." src/

# Find any type usage
grep -rn ": any" src/

# Find unused imports
npx eslint --rule 'no-unused-vars: error'

# Check complexity
npx complexity-report src/
```

### Check Coverage

```bash
# Run coverage
npm run test:coverage

# View coverage report
open coverage/lcov-report/index.html
```

### Security Scan

```bash
# Run security audit
npm audit

# Check for secrets
git secrets --scan

# Dependency vulnerabilities
npm audit fix --dry-run
```

## Integration with QuickAgents

### Before Review
```markdown
1. Check Docs/TASKS.md for task requirements
2. Check Docs/DESIGN.md for architecture decisions
3. Check Docs/MEMORY.md for context
4. Understand what was changed
```

### During Review
```markdown
1. Run through review checklist
2. Identify issues by category
3. Note severity of each issue
4. Suggest fixes for critical issues
```

### After Review
```markdown
1. Generate review report
2. Update Docs/MEMORY.md with findings
3. Log lessons learned
4. Suggest improvements for future
```

## Review Report Template

```markdown
# Code Review Report

**Date**: 2026-03-25
**Reviewer**: AI Agent
**Files Changed**: 5
**Additions**: +150
**Deletions**: -30

---

## Summary

[Brief overview of the changes and overall assessment]

---

## Critical Issues 🔴

### 1. [Issue Title]
- **File**: `src/auth/login.ts:45`
- **Category**: Security
- **Issue**: Password is logged to console
- **Fix**: Remove console.log statement

---

## Warnings 🟡

### 1. [Issue Title]
- **File**: `src/utils/format.ts:12`
- **Category**: Quality
- **Issue**: Magic number used
- **Suggestion**: Extract to named constant

---

## Suggestions 🟢

### 1. [Issue Title]
- **File**: `src/services/api.ts`
- **Category**: Performance
- **Suggestion**: Consider caching repeated calls

---

## Positive Notes ✅

- Good test coverage on auth module
- Clear naming conventions followed
- Proper error handling in API calls

---

## Test Coverage

| File | Coverage | Status |
|------|----------|--------|
| auth/login.ts | 95% | ✅ |
| utils/format.ts | 80% | ✅ |
| services/api.ts | 60% | ⚠️ |

---

## Security Checklist

- [x] No secrets in code
- [x] Input validation present
- [x] Authentication checks correct
- [x] No SQL injection vulnerabilities
- [ ] ~~Remove debug logging~~ (Critical issue)

---

## Recommendations

1. **Immediate**: Fix critical security issue
2. **Soon**: Increase API test coverage
3. **Future**: Consider extracting constants

---

## Approval Status

- [ ] Approved - Ready to merge
- [ ] Changes Requested - Fix critical issues
- [ ] Needs Discussion - Review with team
```

## Best Practices

1. **Be Constructive**: Focus on improvement, not criticism
2. **Be Specific**: Point to exact lines and issues
3. **Explain Why**: Help understand the reasoning
4. **Suggest Solutions**: Don't just identify problems
5. **Prioritize**: Distinguish critical from nice-to-have
6. **Acknowledge Good Work**: Note what's done well
7. **Stay Consistent**: Apply same standards throughout
8. **Consider Context**: Factor in constraints and deadlines
9. **Keep Learning**: Update checklist based on findings
10. **Document Patterns**: Note recurring issues for training

## Resources

- Template: `./assets/review-template.md`
- Examples: `./references/example-reviews.md`
- Checklist: `./references/review-checklist.md`
- Superpowers Reference: https://github.com/obra/superpowers
