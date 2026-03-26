---
name: tdd-workflow-skill
description: |
  Enforce Test-Driven Development (TDD) workflow with strict RED-GREEN-REFACTOR
  cycle. Based on superpowers methodology. Ensures no production code is written
  without a failing test first.
license: MIT
allowed-tools:
  - read
  - write
  - edit
  - bash
  - glob
  - grep
metadata:
  category: development
  priority: critical
  version: 1.0.0
---

# TDD Workflow Skill

## Overview

Enforce strict Test-Driven Development practices. The core principle:
**NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST**.

This skill guides AI agents through the RED-GREEN-REFACTOR cycle and prevents
common TDD violations like writing code before tests or skipping the refactor phase.

## When to Use This Skill

Use this skill when:
- Starting to implement a new feature
- Writing any production code
- Fixing a bug (write failing test first)
- Refactoring existing code
- Before any code commit
- User requests TDD guidance

## The RED-GREEN-REFACTOR Cycle

### Phase 1: RED (Write Failing Test)

**Purpose**: Define expected behavior before implementation

**Steps**:
```
1. Identify the smallest unit of functionality
2. Write a test that describes expected behavior
3. Run the test - it MUST FAIL
4. If test passes, you're testing wrong thing or feature exists
5. Commit to the test (don't modify it to make pass later)
```

**Test Template**:
```typescript
describe('FeatureName', () => {
  describe('methodName', () => {
    it('should [expected behavior] when [condition]', () => {
      // Arrange
      const input = 'test data';

      // Act
      const result = functionUnderTest(input);

      // Assert
      expect(result).toBe('expected output');
    });
  });
});
```

**RED Phase Checklist**:
- [ ] Test file created
- [ ] Test describes ONE behavior
- [ ] Test runs and FAILS
- [ ] Failure message is clear and meaningful
- [ ] No production code written yet

### Phase 2: GREEN (Make Test Pass)

**Purpose**: Write minimal code to pass the test

**Steps**:
```
1. Write the SIMPLEST code that makes test pass
2. Don't worry about clean code yet
3. Hardcoded values are acceptable if they pass the test
4. Run test - it MUST PASS
5. If multiple tests fail, make them pass one at a time
```

**GREEN Phase Principles**:
- Write ONLY enough code to pass
- Don't add features not tested
- Don't optimize yet
- It's OK to be ugly

**GREEN Phase Checklist**:
- [ ] Production code written
- [ ] All tests pass
- [ ] No extra features added
- [ ] Code is minimal (not necessarily clean)

### Phase 3: REFACTOR (Clean Up)

**Purpose**: Improve code quality while keeping tests green

**Steps**:
```
1. Identify code smells (duplication, long methods, etc.)
2. Make one small refactoring change
3. Run tests - they MUST STILL PASS
4. If tests fail, undo and try different approach
5. Repeat until code is clean
6. Commit the refactored version
```

**Common Refactorings**:
- Extract method/function
- Rename variables for clarity
- Remove duplication
- Simplify conditionals
- Extract constants

**REFACTOR Phase Checklist**:
- [ ] Code smells identified
- [ ] Refactoring applied incrementally
- [ ] All tests still pass after each change
- [ ] Code follows project style guide
- [ ] No behavior changed

## TDD Anti-Patterns (FORBIDDEN)

### ❌ Anti-Pattern 1: Code First, Test Later

```
WRONG:
1. Write production code
2. Write test to match code
3. Run test (passes trivially)

CORRECT:
1. Write failing test
2. Write code to make test pass
3. Refactor
```

### ❌ Anti-Pattern 2: Skip the RED Phase

```
WRONG:
1. Write test that already passes
2. Write code

CORRECT:
1. Write test that FAILS
2. Verify failure
3. Write code
```

### ❌ Anti-Pattern 3: Big Bang Testing

```
WRONG:
1. Write 10 tests at once
2. Write all production code
3. Run all tests

CORRECT:
1. Write ONE failing test
2. Make it pass
3. Refactor
4. Repeat for next test
```

### ❌ Anti-Pattern 4: Testing Implementation Details

```
WRONG:
it('should call internal helper method', () => {
  expect(service.internalHelper).toHaveBeenCalled();
});

CORRECT:
it('should return processed data', () => {
  const result = service.process('input');
  expect(result).toBe('expected output');
});
```

### ❌ Anti-Pattern 5: Skipping Refactor

```
WRONG:
1. RED
2. GREEN
3. Commit ugly code

CORRECT:
1. RED
2. GREEN
3. REFACTOR
4. Commit clean code
```

## TDD Workflow Integration

### Before Starting Feature

```markdown
1. Read Docs/TASKS.md for feature requirements
2. Break down feature into smallest testable units
3. Create feature branch
4. Identify first unit to test
```

### During Development

```markdown
Loop until feature complete:
  1. RED: Write one failing test
  2. Verify test fails (run test suite)
  3. GREEN: Write minimal code to pass
  4. Verify all tests pass
  5. REFACTOR: Clean up code
  6. Verify tests still pass
  7. Commit if meaningful progress
```

### Before Commit

```markdown
1. Run ALL tests (not just new ones)
2. Ensure 100% tests pass
3. Check code coverage
4. Run lint/typecheck
5. Update documentation if needed
6. Commit with conventional message
```

## Test Coverage Standards

### Coverage Requirements

| Code Type | Minimum Coverage |
|-----------|------------------|
| Core Logic | 100% |
| Business Logic | 100% |
| Utility Functions | 100% |
| UI Components | 80% |
| Configuration | 50% |
| Integration | As needed |

### Coverage Commands

```bash
# Run tests with coverage
npm run test -- --coverage

# Check coverage threshold
npm run test -- --coverage --coverageThreshold='{"global":{"branches":80,"functions":80,"lines":80}}'
```

## Debugging with TDD

### When Test Fails Unexpectedly

```
1. Don't immediately fix the test
2. Understand WHY it fails
3. Is it a bug in code or test?
4. If bug in code: fix code (test is correct)
5. If bug in test: fix test (but be careful)
6. If requirement changed: update test, then code
```

### Systematic Debugging Process

```
Phase 1: Reproduce
- Isolate the failing test
- Run in isolation
- Confirm consistent failure

Phase 2: Analyze
- Read error message carefully
- Check test assumptions
- Check code assumptions

Phase 3: Hypothesize
- Form theory about cause
- Write test to verify theory

Phase 4: Fix
- Make minimal fix
- Verify all tests pass
- Document the fix
```

## TDD for Bug Fixes

### Bug Fix Workflow

```
1. REPRODUCE: Confirm bug exists
2. TEST: Write test that fails due to bug
3. VERIFY: Test fails for right reason
4. FIX: Write code to fix bug
5. VERIFY: Test passes
6. CHECK: All other tests still pass
7. COMMIT: With reference to bug report
```

**Bug Test Template**:
```typescript
describe('Bug Fix: [Bug Description]', () => {
  it('should [correct behavior] instead of [bug behavior]', () => {
    // This test fails before fix, passes after
    const result = buggyFunction('input');
    expect(result).toBe('correct output');
  });
});
```

## Integration with QuickAgents

### Pre-Development Check
```markdown
1. Check Docs/TASKS.md for current task
2. Check Docs/MEMORY.md for context
3. Verify no blockers
4. Identify test file location
```

### During TDD Cycle
```markdown
1. Log progress to Working Memory
2. Update TASKS.md on task completion
3. Record any decisions to DECISIONS.md
4. Note any lessons learned
```

### Post-Feature Completion
```markdown
1. Update Experiential Memory
2. Record TDD insights
3. Update documentation
4. Generate cross-session handoff
```

## Test File Organization

### Directory Structure

```
project/
├── src/
│   ├── features/
│   │   └── auth/
│   │       ├── login.ts
│   │       └── login.test.ts    ← Co-located tests
│   └── utils/
│       ├── format.ts
│       └── format.test.ts
├── tests/
│   ├── integration/
│   └── e2e/
└── ...
```

### Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Unit Test | `*.test.ts` | `login.test.ts` |
| Integration | `*.integration.test.ts` | `api.integration.test.ts` |
| E2E | `*.e2e.test.ts` | `checkout.e2e.test.ts` |

## Common Test Patterns

### AAA Pattern (Arrange-Act-Assert)

```typescript
it('should calculate total with tax', () => {
  // Arrange
  const items = [{ price: 100 }, { price: 50 }];
  const taxRate = 0.1;

  // Act
  const total = calculateTotal(items, taxRate);

  // Assert
  expect(total).toBe(165); // (100 + 50) * 1.1
});
```

### Given-When-Then (BDD Style)

```typescript
it('should allow user to login with valid credentials', () => {
  // Given
  const user = { email: 'test@example.com', password: 'valid' };
  mockDb.findUser.mockResolvedValue(user);

  // When
  const result = await login(user.email, user.password);

  // Then
  expect(result.success).toBe(true);
  expect(result.token).toBeDefined();
});
```

## Best Practices

1. **One assertion per test** (when practical)
2. **Test behavior, not implementation**
3. **Use descriptive test names**
4. **Keep tests independent**
5. **Don't test external libraries**
6. **Mock external dependencies**
7. **Test edge cases and errors**
8. **Make tests fast**
9. **Run tests frequently**
10. **Never skip failing tests**

## Verification Commands

```bash
# Run all tests
npm test

# Run specific test file
npm test -- login.test.ts

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch

# Type check
npm run typecheck

# Lint
npm run lint
```

## Resources

- Template: `./assets/test-template.ts`
- Examples: `./references/example-tests.md`
- Superpowers Reference: https://github.com/obra/superpowers
