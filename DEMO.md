# COL Demo Walkthrough

A step-by-step terminal demonstration of the Context Orchestration Layer.

## Prerequisites

```bash
# Activate the environment
conda activate col

# Ensure API keys are set
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
```

## Demo Scenario: Designing a REST API

This demo shows how to use COL to design a REST API, switching providers mid-task.

### Step 1: Initialize the Context

```bash
col init demo_task.json
```

**Expected output:**
```
Created context file: demo_task.json

Edit this file to set your goal, constraints, and initial facts.
```

### Step 2: Set Up the Task

Edit `demo_task.json`:

```json
{
  "goal": "Design a REST API for a todo list application",
  "constraints": [
    "Must use JSON for request/response bodies",
    "Must follow RESTful conventions",
    "Must support CRUD operations"
  ],
  "facts": [
    "Target users are web and mobile developers",
    "Expected scale is under 1000 concurrent users"
  ],
  "decisions": [],
  "tool_outputs": [],
  "open_questions": []
}
```

### Step 3: Brainstorm with OpenAI

```bash
col run --context demo_task.json --provider openai --instruction "What endpoints should we define?"
```

**Expected output:**
```
Running with openai...
Prompt hash: a1b2c3d4e5f6g7h8

Answer:
╭──────────────────────────────────────────────────────────────────────────────╮
│ Based on your requirements, I recommend the following endpoints...           │
│ [detailed response about endpoints]                                          │
╰──────────────────────────────────────────────────────────────────────────────╯

Suggested Context Updates:
Facts: ['REST API will have 5 core endpoints', ...]
Decisions: ['Use /api/v1 prefix for versioning', ...]
Open Questions: ['Should we support batch operations?', ...]

To apply these updates, run:
  col apply --context demo_task.json --response response.json

Response saved to: response.json
```

### Step 4: Apply the Updates

```bash
col apply --context demo_task.json --response response.json
```

**Expected output:**
```
Changes to be applied
├── facts
│   └── + REST API will have 5 core endpoints
│   └── + ...
├── decisions
│   └── + Use /api/v1 prefix for versioning
│   └── + ...
└── open_questions
    └── + Should we support batch operations?

Apply these changes? [y/n]: y

Context updated: demo_task.json
```

### Step 5: Validate with Anthropic

Now switch to a different provider to get a second opinion:

```bash
col run --context demo_task.json --provider anthropic --instruction "Review the API design. Are there any gaps or improvements?"
```

**Expected output:**
```
Running with anthropic...
Prompt hash: b2c3d4e5f6g7h8i9

Answer:
╭──────────────────────────────────────────────────────────────────────────────╮
│ The API design looks solid. A few suggestions...                             │
│ [detailed review and suggestions]                                            │
╰──────────────────────────────────────────────────────────────────────────────╯

Suggested Context Updates:
Facts: [...]
Decisions: [...]

To apply these updates, run:
  col apply --context demo_task.json --response response.json

Response saved to: response.json
```

### Step 6: Apply Selected Updates

```bash
col apply --context demo_task.json --response response.json
```

Review and approve/reject the suggestions.

### Step 7: Check Metrics

```bash
col metrics --context demo_task.json
```

**Expected output:**
```
       Context Metrics        
┏━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Field          ┃ Count ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━┩
│ Goal           │     1 │
│ Constraints    │     3 │
│ Facts          │     5 │
│ Decisions      │     4 │
│ Tool Outputs   │     0 │
│ Open Questions │     2 │
└────────────────┴───────┘

File size: 1,234 bytes
System prompt chars: 2,456
Estimated tokens: ~614
```

### Step 8: Validate the Context File

```bash
col validate demo_task.json
```

**Expected output:**
```
Valid: demo_task.json
  Goal: (set)
  Constraints: 3
  Facts: 5
  Decisions: 4
  Tool Outputs: 0
  Open Questions: 2
```

## Key Observations

1. **Provider Switching** - The same context file worked with both OpenAI and Anthropic
2. **User Control** - Each update required explicit approval via `col apply`
3. **Transparency** - The context file is plain JSON, readable and editable
4. **Prompt Hash** - Enables verification that the same context produces identical prompts
5. **No Hidden State** - Everything is in the context file

## Cleanup

```bash
rm demo_task.json response.json
rm -rf .col/
```

## Verifying Determinism

To verify that prompt rendering is deterministic:

```bash
# Run twice with the same context (without API call)
col metrics --context demo_task.json
col metrics --context demo_task.json
```

The "System prompt chars" should be identical.
