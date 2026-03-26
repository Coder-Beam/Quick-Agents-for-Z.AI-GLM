---
name: inquiry-skill
description: |
  Use when starting a new project or feature to guide systematic requirement
  clarification through 7-layer progressive inquiry model. Ensures 100% requirement
  clarity before development begins.
license: MIT
allowed-tools:
  - read
  - write
  - todowrite
metadata:
  category: requirements
  priority: critical
  version: 1.0.0
---

# 7-Layer Progressive Inquiry Skill

## Overview

Guide AI agents through a systematic, layered questioning process to achieve 100%
requirement clarity before development begins. Based on the principle that unclear
requirements lead to failed projects.

## When to Use This Skill

Use this skill when:
- Starting a new project
- Beginning a new feature
- User provides vague or incomplete requirements
- User says "build something like X"
- Before making architectural decisions

## The 7 Layers

### L1: Business Essence (业务本质)

**Goal**: Understand why we're building this

**Key Questions**:
1. What is the core pain point this solves?
2. What business value does this create?
3. How do we measure success?

**Exit Criteria**:
- ✅ Pain point clearly identified
- ✅ Business value quantified
- ✅ Success metrics defined

**Example**:
```
User: "I want to build an e-commerce platform"

AI (L1 Inquiry):
- What specific problem are you trying to solve?
- Who is experiencing this problem?
- How will you know if the platform is successful?

User: "Small businesses struggle to sell online. Success = 1000 merchants in 6 months"

✅ L1 Complete
```

### L2: User Persona (用户画像)

**Goal**: Understand who will use this

**Key Questions**:
1. Who are the primary users?
2. What are their characteristics?
3. What are their goals and motivations?

**Exit Criteria**:
- ✅ Primary user segments identified
- ✅ User characteristics documented
- ✅ User goals understood

**Example**:
```
AI (L2 Inquiry):
- Who are the primary merchants? (age, technical skill, business size)
- Who are the end customers?
- What motivates them to use this platform?

User: "Merchants are 25-45yo, non-technical, small business owners. 
       Customers are general consumers looking for unique products"

✅ L2 Complete
```

### L3: Core Workflow (核心流程)

**Goal**: Map the complete user journey

**Key Questions**:
1. What is the primary user journey?
2. What are the key interactions?
3. What happens at each step?

**Exit Criteria**:
- ✅ Main workflow documented
- ✅ Key touchpoints identified
- ✅ User actions defined

**Example**:
```
AI (L3 Inquiry):
- Walk me through a merchant signing up and listing a product
- Walk me through a customer discovering and buying a product
- What happens after a purchase?

User: "Merchant: signup → add store → list products → receive orders → ship
       Customer: browse → search → add to cart → checkout → receive"

✅ L3 Complete
```

### L4: Feature List (功能清单)

**Goal**: Define what to build

**Key Questions**:
1. What features are absolutely necessary?
2. What features are nice to have?
3. What features can wait?

**Exit Criteria**:
- ✅ MVP features listed
- ✅ Priority assigned to each feature
- ✅ Feature boundaries defined

**Example**:
```
AI (L4 Inquiry):
- What features are needed for MVP?
- What can we add in v2?
- Any features we should explicitly exclude?

User: "MVP: product listing, cart, checkout, order management
       v2: reviews, recommendations, analytics
       Exclude: auctions, subscriptions"

✅ L4 Complete
```

### L5: Data Model (数据模型)

**Goal**: Understand data requirements

**Key Questions**:
1. What are the main data entities?
2. How do they relate to each other?
3. What data needs to be stored?

**Exit Criteria**:
- ✅ Main entities identified
- ✅ Relationships mapped
- ✅ Data volume estimated

**Example**:
```
AI (L5 Inquiry):
- What information do we need for products?
- How are orders related to users and products?
- Any special data requirements (images, files, etc.)?

User: "Products: name, description, price, images, inventory
       Orders: user, items, total, status, shipping address
       Need to store product images"

✅ L5 Complete
```

### L6: Tech Stack (技术栈)

**Goal**: Determine technical approach

**Key Questions**:
1. What frontend framework?
2. What backend framework?
3. What database?
4. Any specific technical constraints?

**Exit Criteria**:
- ✅ Frontend technology selected
- ✅ Backend technology selected
- ✅ Database selected
- ✅ Deployment strategy defined

**Example**:
```
AI (L6 Inquiry):
- Do you have a preferred frontend framework?
- Backend language preference?
- Any existing infrastructure or constraints?

User: "React for frontend, Node.js for backend, PostgreSQL
       Must deploy to AWS, 3-month timeline, 4-person team"

✅ L6 Complete
```

### L7: Delivery Standards (交付标准)

**Goal**: Define acceptance criteria

**Key Questions**:
1. What are the acceptance criteria?
2. What is the timeline?
3. What quality standards must be met?

**Exit Criteria**:
- ✅ Acceptance criteria documented
- ✅ Timeline established
- ✅ Quality standards defined

**Example**:
```
AI (L7 Inquiry):
- How will you test if the platform meets your needs?
- What is your target launch date?
- Any specific performance or security requirements?

User: "Test: 10 merchants can list and sell products end-to-end
       Launch: 3 months from now
       Performance: <2s page load, 99.9% uptime"

✅ L7 Complete
```

## Inquiry Process

### Quick Mode (Default)

For most projects, use quick mode:

```
1. Start with L1-L3 (10-15 min)
2. Confirm critical decisions (2-3 questions)
3. Generate configuration
4. User can add details later
```

### Deep Mode

For complex projects, use deep mode:

```
1. Complete all 7 layers (30-60 min)
2. Generate comprehensive documentation
3. Risk assessment
4. Detailed implementation plan
```

### Adaptive Mode

Adjust based on project complexity:

| Complexity | Layers | Time | Questions |
|------------|--------|------|-----------|
| Simple | L1-L4 | 10 min | 5-8 |
| Medium | L1-L6 | 20 min | 10-15 |
| Complex | L1-L7 | 40 min | 20-30 |

## Question Generation

### Principles

1. **One concept per question**: Don't ask compound questions
2. **Provide context**: Explain why you're asking
3. **Offer examples**: Help user understand what you need
4. **Allow skip**: Let users defer non-critical questions
5. **Confirm understanding**: Repeat back what you heard

### Template

```markdown
## Round N - [Layer Name]

**Current Goal**: [What we're trying to understand]

**Key Questions**:
1. [Question 1]
   - Context: [Why this matters]
   - Example: [If unsure, consider X]

2. [Question 2]
   - Context: [Why this matters]
   - Example: [If unsure, consider X]

**Confirmed So Far**:
- ✅ [Confirmed point 1]
- ✅ [Confirmed point 2]

**Layers Status**:
- [x] L1 Business Essence
- [x] L2 User Persona
- [ ] L3 Core Workflow
- [ ] L4 Feature List
- [ ] L5 Data Model
- [ ] L6 Tech Stack
- [ ] L7 Delivery Standards
```

## Exit Conditions

Stop inquiry when:

1. **User confirms**: User says "that's enough", "continue", "start"
2. **All layers complete**: 7 layers fully clarified
3. **AI judges sufficient**: Information is enough to proceed

## Common Patterns

### Pattern 1: Vague Initial Request

```
User: "Build me something cool"

AI: Start with L1 (Business Essence)
- "What problem are you trying to solve?"
- "Who is this for?"
- "What would make you say 'this is successful'?"

[Continue layer by layer until clarity achieved]
```

### Pattern 2: Technical-First User

```
User: "I need a React + Node.js app with PostgreSQL"

AI: Acknowledge tech choice, go to L1
- "Great tech stack! What are we building with it?"
- "What problem will this solve?"
[Continue with business questions]
```

### Pattern 3: Feature-First User

```
User: "I need user authentication and payment processing"

AI: Acknowledge features, seek context
- "Understood. What kind of application needs these features?"
- "Who are the users that will authenticate?"
[Continue with business questions]
```

## Integration with QuickAgents

### Before Inquiry

1. Check `MEMORY.md` for existing project context
2. Check if user has provided requirements file
3. Determine appropriate inquiry mode

### During Inquiry

1. Log each layer completion to `MEMORY.md` Working Memory
2. Track confirmed decisions in `DECISIONS.md`
3. Update task list in `TASKS.md`

### After Inquiry

1. Generate `AGENTS.md` with all collected information
2. Create `Docs/MEMORY.md` with project facts
3. Create `Docs/DESIGN.md` with architecture decisions
4. Create `Docs/TASKS.md` with feature breakdown

## Best Practices

1. **Start with why**: Always begin with business essence
2. **Listen actively**: Don't assume, ask for clarification
3. **Be patient**: Take time to understand completely
4. **Document everything**: Write down all decisions
5. **Validate understanding**: Repeat back what you heard
6. **Stay focused**: One layer at a time
7. **Adapt to user**: Some users want deep detail, others want speed

## Resources

- Template: `./assets/inquiry-card-template.md`
- Examples: `./references/example-sessions.md`
- Quick Reference: `./references/layer-quick-ref.md`
