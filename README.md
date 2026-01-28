# Context Orchestration Layer (COL)

A standalone, model-agnostic context engine that preserves structured task state and allows seamless switching between LLM providers without losing progress.

## Why This Exists

Most LLM tools conflate "context" with "chat history." COL takes a different approach:

- **Context is explicit** - A structured JSON object, not hidden state
- **Context is visible** - The file on disk is the only source of truth
- **Context is portable** - Switch from OpenAI to Claude mid-task without losing progress
- **User controls mutations** - Models suggest changes, you decide what to apply

## Installation

```bash
# Create conda environment
conda create -n col python=3.11
conda activate col

# Install dependencies
pip install -r requirements.txt

# Install COL
pip install -e .
```

## Configuration

Set your API keys as environment variables:

```bash
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
export GROQ_API_KEY="your-key"
```

Optionally create a `col.yaml` in your working directory for defaults:

```yaml
default_provider: openai  # or anthropic, groq
default_model: gpt-4o     # provider-specific model name
default_context_file: context.json
default_output_file: response.json
```

**How col.yaml works:**
- Place it in your working directory (where you run `col` commands)
- Settings override built-in defaults
- Environment variables override file settings
- CLI flags override everything

Priority (highest to lowest):
1. CLI flags (e.g., `--provider openai`)
2. Environment variables (e.g., `COL_DEFAULT_PROVIDER`)
3. `col.yaml` settings
4. Built-in defaults

## Usage

### Initialize a Context

```bash
col init task.json
```

Creates a new context file with this structure:

```json
{
  "goal": "",
  "constraints": [],
  "facts": [],
  "decisions": [],
  "tool_outputs": [],
  "open_questions": []
}
```

Edit this file to set your goal, constraints, and initial facts.

### Run a Completion

```bash
col run --context task.json --provider openai --prompt "What's the best approach?"

# Or use Anthropic
col run --context task.json --provider anthropic --prompt "What's the best approach?"

# Or use Groq
col run --context task.json --provider groq --prompt "What's the best approach?"
```

The model responds with an answer and suggested context updates. The context file is NOT modified.

### Apply Updates

```bash
col apply --context task.json --response response.json
```

Review and approve the suggested changes. Only approved changes are added to the context.

### Check Metrics

```bash
col metrics --context task.json
```

Shows context size, item counts, and estimated token usage.

### Switch Providers Mid-Task

```bash
# Start with OpenAI
col run --context task.json --provider openai --prompt "Design the API"
col apply --context task.json --response response.json

# Continue with Claude
col run --context task.json --provider anthropic --prompt "Now implement it"
col apply --context task.json --response response.json

# Continue with Groq
col run --context task.json --provider groq --prompt "Review and optimize"
```

The context file works with any provider. No conversion needed.

## Context Schema

```json
{
  "goal": "The primary objective",
  "constraints": ["Hard constraints on the solution"],
  "facts": ["Established facts about the problem"],
  "decisions": ["Decisions that have been made"],
  "tool_outputs": ["Results from external tools (added manually)"],
  "open_questions": ["Unresolved questions"]
}
```

## Model Response Format

Models must return:

```json
{
  "answer": "The response",
  "suggested_context_updates": {
    "facts": [],
    "decisions": [],
    "constraints": [],
    "tool_outputs": [],
    "open_questions": []
  }
}
```

## Design Principles

1. **No chat history** - Only the structured context
2. **No embeddings** - No vector database, no RAG
3. **No hidden state** - The JSON file is everything
4. **No automation** - COL stops after every response
5. **Append-only** - New items are added, never deleted automatically
6. **User authority** - You approve all changes

## What COL is NOT

- An agent framework
- A tool-calling platform
- A memory system with hidden state
- A chat interface

## License

MIT
