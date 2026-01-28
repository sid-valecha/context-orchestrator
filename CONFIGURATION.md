# COL Configuration Guide

## How col.yaml Works

### Configuration Priority

COL uses a layered configuration system with the following priority (highest to lowest):

1. **CLI flags** - Direct command-line arguments
2. **Environment variables** - Shell environment settings
3. **col.yaml file** - Project-specific configuration
4. **Built-in defaults** - Hardcoded fallbacks

### Configuration File Location

Place `col.yaml` in the directory where you run `col` commands. COL looks for it in your current working directory.

```bash
my-project/
├── col.yaml          # Configuration file
├── context.json      # Your context
└── response.json     # Model responses
```

### Configuration Schema

```yaml
# Default LLM provider (required if you don't pass --provider flag)
default_provider: openai  # Options: openai, anthropic, groq

# Default model for the provider (optional, uses provider defaults if omitted)
default_model: gpt-4o

# Default context filename (optional, defaults to "context.json")
default_context_file: context.json

# Default output filename (optional, defaults to "response.json")
default_output_file: response.json
```

### Example Configurations

#### For OpenAI-focused projects:
```yaml
default_provider: openai
default_model: gpt-4o
```

#### For Anthropic-focused projects:
```yaml
default_provider: anthropic
default_model: claude-sonnet-4-20250514
```

#### For Groq-focused projects:
```yaml
default_provider: groq
default_model: llama-3.3-70b-versatile
```

#### Multi-context setup:
```yaml
default_provider: openai
default_context_file: main_task.json
default_output_file: main_response.json
```

### Environment Variable Overrides

You can override config file settings with environment variables:

```bash
# Override the default provider
export COL_DEFAULT_PROVIDER=anthropic

# Override the default model
export COL_DEFAULT_MODEL=claude-opus-4-20250514

# Override default filenames
export COL_DEFAULT_CONTEXT_FILE=my_context.json
export COL_DEFAULT_OUTPUT_FILE=my_response.json
```

### API Keys (Required)

API keys are **always** read from environment variables:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GROQ_API_KEY="gsk_..."
```

These are never stored in `col.yaml` or any file.

### Complete Example Workflow

1. **Create col.yaml:**
```yaml
default_provider: openai
default_model: gpt-4o
default_context_file: task.json
```

2. **Set API key:**
```bash
export OPENAI_API_KEY="your-key"
```

3. **Use defaults (no flags needed):**
```bash
# Uses settings from col.yaml
col run --prompt "What's next?"
```

4. **Override when needed:**
```bash
# Override provider with CLI flag
col run --provider anthropic --prompt "What's next?"

# Override with env var (for this session)
COL_DEFAULT_PROVIDER=groq col run --prompt "What's next?"
```

### When to Use Each Method

**CLI flags:**
- One-off provider switches
- Testing different models
- Explicit control

**Environment variables:**
- CI/CD environments
- Per-session overrides
- Development vs production separation

**col.yaml:**
- Project defaults
- Team consistency
- Less typing in daily use

**Built-in defaults:**
- Quick starts
- No configuration needed
- Fallback behavior

## Supported Providers and Models

### OpenAI
- `gpt-4o` (default)
- `gpt-4-turbo`
- `gpt-4`
- `gpt-3.5-turbo`

### Anthropic
- `claude-sonnet-4-20250514` (default)
- `claude-opus-4-20250514`
- `claude-3-5-sonnet-20241022`

### Groq
- `llama-3.3-70b-versatile` (default)
- `mixtral-8x7b-32768`
- `llama-3.1-70b-versatile`

Check each provider's documentation for the latest available models.

## Setup Instructions

### 1. Copy the example:
```bash
cp col.yaml.example col.yaml
```

### 2. Edit for your needs:
```bash
nano col.yaml  # or vim, code, etc.
```

### 3. Set your API keys:
```bash
# Add to ~/.zshrc for persistence
echo 'export OPENAI_API_KEY="your-key"' >> ~/.zshrc
echo 'export ANTHROPIC_API_KEY="your-key"' >> ~/.zshrc
echo 'export GROQ_API_KEY="your-key"' >> ~/.zshrc
source ~/.zshrc
```

### 4. Test it:
```bash
col init
col run --prompt "test"
```

## Troubleshooting

### "Unknown provider" error
- Check `default_provider` spelling in col.yaml
- Ensure it's one of: `openai`, `anthropic`, `groq`

### API key errors
- Verify environment variable name matches: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GROQ_API_KEY`
- Check key is exported: `echo $OPENAI_API_KEY`
- Ensure no quotes or spaces in the key

### Config not loading
- Verify `col.yaml` is in current directory: `ls col.yaml`
- Check YAML syntax is valid
- Try with explicit flags first: `col run --provider openai ...`
