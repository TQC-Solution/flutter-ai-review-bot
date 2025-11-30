# Flutter AI Code Reviewer (OpenRouter)

> **🎉 NEW: v3.0 - OpenRouter Integration!** Now supports multiple AI providers through OpenRouter API. Easily switch between models like Grok, Claude, GPT-4, Gemini, and more by just changing a config parameter. No more vendor lock-in!

Automated GitHub Pull Request reviewer for **Flutter/Dart** projects using **OpenRouter AI** (supports 200+ models).

This action reviews Flutter code based on Clean Architecture principles, GetX best practices, and comprehensive coding standards. It posts **one consolidated AI review comment** on each Pull Request with specific, actionable feedback.

## Features

- ✅ **200+ AI Models Support**: Use any model from OpenRouter (Grok, Claude, GPT-4, Gemini, Llama, Mistral, etc.)
- ✅ **Easy Model Switching**: Change AI provider with just one config parameter - no code changes needed
- ✅ **Free & Paid Options**: Choose from free models (Grok 4.1, Gemini 2.0) or premium ones (Claude 3.5, GPT-4)
- ✅ **Reasoning Support**: Enable advanced reasoning for supported models (e.g., Grok 4.1)
- ✅ **Intelligent Chunking**: Automatically splits large PRs (>5 files, >30k chars) into reviewable chunks to ensure complete coverage
- ✅ **Clean Architecture Review**: Validates layer dependencies and architectural patterns
- ✅ **GetX Best Practices**: Checks controller lifecycle and instance management
- ✅ **Type Safety**: Detects hardcoded assets and translation strings
- ✅ **Multi-language Support**: Review comments in Vietnamese or English
- ✅ **Modular Rule System**: Coding standards organized in separate rule files for easy maintenance
- ✅ **Single Consolidated Comment**: Posts one comprehensive review per PR to minimize noise
- ✅ **Automatic Retry**: Handles rate limits with exponential backoff

## Usage

### As a GitHub Action (Recommended)

**Quick Setup:**

1. Copy the example workflow from the code block below
2. Create a file `.github/workflows/ai-review.yml` in your repo
3. Paste the content and save
4. That's it! Ready to use.

**Workflow Configuration:**

```yaml
# .github/workflows/ai-review.yml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]
    branches: [main, dev]

permissions:
  contents: read
  pull-requests: write
  issues: write

jobs:
  ai_review:
    name: AI Code Review
    runs-on: ubuntu-latest

    steps:
      - name: Checkout source code
        uses: actions/checkout@v4

      - name: Run OpenRouter AI Code Reviewer
        uses: vincetran/flutter-ai-review-bot@main  # Or use a specific version tag
        with:
          openrouter-api-key: ${{ secrets.OPENROUTER_API_KEY }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
          review-language: 'vietnamese'  # Optional: 'vietnamese' or 'english' (default: vietnamese)
```

### Setup

1. **Get an OpenRouter API Key**
   - Visit [OpenRouter Keys](https://openrouter.ai/keys)
   - Sign up and create a new API key
   - Add credits if using paid models (many free models available!)

2. **Add GitHub Secret**
   - Go to your repository **Settings → Secrets and variables → Actions**
   - Click **New repository secret**
   - Name: `OPENROUTER_API_KEY`
   - Value: Your OpenRouter API key from step 1

3. **Create a Pull Request**
   - The action will automatically run and post a review comment

### Model Configuration

**Note**: The AI model is controlled by this project's maintainers. Users cannot change the model through workflow configuration.

**Current Model**: `x-ai/grok-4.1-fast:free` (Free, fast, supports reasoning)

To change the model, project maintainers should edit [`scripts/reviewer/config.py`](scripts/reviewer/config.py):

```python
# Line 28 in config.py
OPENROUTER_MODEL = "x-ai/grok-4.1-fast:free"  # Change this value

# Available options:
# Free: "x-ai/grok-4.1-fast:free", "google/gemini-2.0-flash-exp:free"
# Paid: "anthropic/claude-3.5-sonnet", "openai/gpt-4-turbo"
```

See [OpenRouter Model List](https://openrouter.ai/models) for all available models and pricing.

## Configuration Options

### Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `openrouter-api-key` | Yes | - | OpenRouter API key for AI code review |
| `github-token` | Yes | - | GitHub token (use `${{ secrets.GITHUB_TOKEN }}`) |
| `review-language` | No | `vietnamese` | Review comment language: `vietnamese` or `english` |

### Examples

#### English Reviews

```yaml
- uses: vincetran/flutter-ai-review-bot@main
  with:
    openrouter-api-key: ${{ secrets.OPENROUTER_API_KEY }}
    github-token: ${{ secrets.GITHUB_TOKEN }}
    review-language: 'english'
```

## Review Criteria

The AI reviewer checks for:

1. **Architecture Violations**
   - Domain layer importing Data/Presentation layers
   - Incorrect layer dependencies

2. **GetX Controller Management**
   - Improper use of `Get.put()` vs `Get.find()`
   - Controller lifecycle issues

3. **Type Safety**
   - Hardcoded asset paths (should use `Assets.icons.iconName`)
   - Hardcoded UI strings (should use `context.tr()`)

4. **Error Handling**
   - Missing `Either<Failure, T>` pattern
   - Raw exceptions instead of Failure types

5. **Naming Conventions**
   - File names (snake_case)
   - Class names (PascalCase)
   - Variables/methods (camelCase)

6. **Code Quality**
   - Bugs and correctness issues
   - Readability and maintainability
   - Performance concerns

## Development

### Project Structure

```
flutter-ai-review-bot/
├── action.yml                           # GitHub Action definition
├── .github/workflows/
│   └── ai-review.yml                   # Workflow for this repo (uses: ./)
├── scripts/
│   ├── ai_review.py                    # Main orchestrator (173 lines)
│   ├── reviewer/                       # Modular package
│   │   ├── __init__.py                # Package exports
│   │   ├── config.py                  # Configuration management
│   │   ├── github_client.py           # GitHub API operations
│   │   ├── gemini_client.py           # Gemini AI integration
│   │   ├── prompt_builder.py          # Prompt construction
│   │   ├── diff_chunker.py            # Intelligent diff chunking (NEW)
│   │   ├── utils.py                   # Helper functions
│   │   ├── README.md                  # Module documentation
│   │   └── ARCHITECTURE.md            # Architecture details
│   ├── requirements.txt                # Python dependencies
│   ├── rule/                           # Modular coding rules
│   │   ├── CLEAN_ARCHITECTURE_RULES.md # Clean Architecture guidelines
│   │   ├── GETX_CONTROLLER_RULES.md    # GetX best practices
│   │   └── CODING_RULES.md             # General coding standards
│   └── prompts/                        # AI prompt templates
│       ├── review_prompt_vi.txt        # Vietnamese prompt
│       ├── review_prompt_en.txt        # English prompt
│       └── README.md                   # Prompt documentation
└── README.md
```

### Architecture (Refactored v2.0)

**The project has been refactored from a monolithic 486-line script into 6 specialized modules:**

#### Main Orchestrator
- **[ai_review.py](scripts/ai_review.py)** (104 lines, **-78.6%** reduction)
  - Coordinates all modules
  - Handles main workflow
  - Minimal, clean code

#### Reviewer Package Modules
1. **[config.py](scripts/reviewer/config.py)** (97 lines)
   - Environment variables management
   - Configuration validation
   - Constants definition (MAX_DIFF_LENGTH: 100k, max_output_tokens: 32k)

2. **[github_client.py](scripts/reviewer/github_client.py)** (267 lines)
   - Fetch PR metadata and diffs
   - Post review comments
   - Diff structure validation (NEW)
   - Handle long reviews with chunking

3. **[openrouter_client.py](scripts/reviewer/openrouter_client.py)** (NEW in v3.0)
   - OpenRouter API integration
   - Support for 200+ models
   - Reasoning support for advanced models
   - API calls with retry logic
   - Rate limit handling

4. **[prompt_builder.py](scripts/reviewer/prompt_builder.py)** (263 lines)
   - Load language-specific templates
   - Load coding guidelines
   - Build complete prompts
   - Smart diff truncation (NEW)
   - Chunked prompt generation (NEW)

5. **[diff_chunker.py](scripts/reviewer/diff_chunker.py)** (169 lines) ⭐ **NEW**
   - Intelligent diff splitting by file boundaries
   - Auto-detect when chunking is needed
   - Prevents "lost in the middle" attention degradation

6. **[utils.py](scripts/reviewer/utils.py)** (88 lines)
   - Parse PR numbers
   - Format errors
   - Helper functions

#### Benefits of New Architecture
- ✅ **Modular**: Each module has a single responsibility
- ✅ **Testable**: Can unit test each module independently
- ✅ **Maintainable**: Easy to find and fix issues
- ✅ **Extensible**: Easy to add new AI providers or features
- ✅ **Backward Compatible**: No changes needed to existing workflows

**Learn More:**
- 📖 [Quick Start Guide](QUICK_START.md) - Get started with the refactored code
- 📖 [Refactoring Details](REFACTORING.md) - Detailed before/after comparison
- 📖 [Module Documentation](scripts/reviewer/README.md) - Deep dive into each module
- 📖 [Architecture Diagrams](scripts/reviewer/ARCHITECTURE.md) - Visual architecture guide

### Local Testing

```bash
# Set environment variables
export GITHUB_REF='refs/pull/1/merge'
export GITHUB_TOKEN='your_github_token'
export GITHUB_REPOSITORY='owner/repo'
export OPENROUTER_API_KEY='your_openrouter_api_key'
export REVIEW_LANGUAGE='vietnamese'  # Optional

# Install dependencies
pip install -r scripts/requirements.txt

# Run the script
python scripts/ai_review.py

# Note: Model is configured in scripts/reviewer/config.py
```

### Customizing the Review Rules

The review rules are organized in modular files in `scripts/rule/`:

- **[CLEAN_ARCHITECTURE_RULES.md](scripts/rule/CLEAN_ARCHITECTURE_RULES.md)** - Clean Architecture principles and layer dependencies
- **[GETX_CONTROLLER_RULES.md](scripts/rule/GETX_CONTROLLER_RULES.md)** - GetX state management best practices
- **[CODING_RULES.md](scripts/rule/CODING_RULES.md)** - General coding standards (naming, assets, i18n, error handling)

**To customize:**
1. Edit the existing rule files to match your project's standards
2. Add new rule files to `scripts/rule/` (they will be automatically loaded)
3. All `.md` files in the `rule/` directory are combined and used for code review

### Customizing Review Prompts

The AI review prompts are stored as separate text files for easy editing:

**Location**: `scripts/prompts/`
- `review_prompt_vi.txt` - Vietnamese prompt template
- `review_prompt_en.txt` - English prompt template

**To customize**:
1. Edit the appropriate `.txt` file directly
2. Use template variables:
   - `{coding_rules}` - Content from your coding guide
   - `{code_diff}` - The PR diff to review
3. No need to modify Python code!

**Example edit**:
```txt
# In review_prompt_vi.txt, change the tone:
Bạn là một friendly senior Flutter/Dart engineer...
```

See [scripts/prompts/README.md](scripts/prompts/README.md) for detailed documentation.

## API Quotas & Pricing

**OpenRouter Pricing:**
- **Free Models**: Many models available at no cost (Grok 4.1, Gemini 2.0 Flash, Llama 3.2, etc.)
- **Paid Models**: Pay-per-token pricing, usually very affordable
  - Example: Claude 3.5 Sonnet ~$0.01-0.02 per review
  - Example: GPT-4 Turbo ~$0.02-0.05 per review

The action automatically:
- Retries with exponential backoff on rate limits
- Handles API errors gracefully
- Supports reasoning for better quality reviews

**Check your usage**: [OpenRouter Dashboard](https://openrouter.ai/activity)

**Model comparison**: See [OpenRouter Models](https://openrouter.ai/models) for detailed pricing and specs

## Large PR Handling

**The action automatically handles large Pull Requests using intelligent chunking:**

### When Chunking is Used
- PRs with **>5 files** AND **>30,000 characters**
- Automatically splits diff by file boundaries (never cuts mid-file)
- Reviews each chunk separately, then merges results

### Benefits
- ✅ **Complete Coverage**: All files reviewed, even in large PRs
- ✅ **No "Lost in the Middle"**: Avoids LLM attention degradation on long context
- ✅ **Better Quality**: AI focuses on 2-4 files at a time for thorough review
- ✅ **Transparent Progress**: Logs show "Reviewing chunk 2/5..." during processing

### Example Output
For large PRs, you'll see a merged review like:

```markdown
## 📋 Tổng Hợp Code Review

_PR này được review theo 3 phần do kích thước lớn._

---

### Phần 1: lib/features/auth/login.dart, logout.dart
🔴 Lỗi Nghiêm Trọng
...

---

### Phần 2: lib/features/profile/user_profile.dart
⚠️ Cảnh báo
...
```

**Note**: Chunked reviews use multiple API calls (1 per chunk) but ensure no code is missed.

## Troubleshooting

### "OPENROUTER_API_KEY not set"
- Make sure you added the secret in repository Settings → Secrets → Actions

### "Invalid API key (401)"
- Verify your OpenRouter API key at [OpenRouter Keys](https://openrouter.ai/keys)
- Make sure the secret name is exactly `OPENROUTER_API_KEY`

### "Insufficient credits (402)"
- Add credits at [OpenRouter Credits](https://openrouter.ai/credits)
- Or switch to a free model (see [Available Models](#available-models))

### "PR diff is empty"
- The PR has no code changes to review

### "Rate limit exceeded (429)"
- Wait a moment and retry (action auto-retries with backoff)
- Check your rate limits at [OpenRouter Settings](https://openrouter.ai/settings/limits)

### "AI says file doesn't exist" or "Missing code review"
These issues have been fixed in the latest version:
- **Smart Truncation**: Diff is cut at file boundaries, not mid-file
- **Intelligent Chunking**: Large PRs (>5 files, >30k chars) automatically split for complete coverage
- **Increased Limits**: Now handles up to 100k characters (was 12k)
- If you still experience issues, check the GitHub Actions logs for chunking information

## License

MIT License - Feel free to use and modify for your projects

## Contributing

Contributions welcome! Please open an issue or PR.

## Credits

Built with:
- [OpenRouter API](https://openrouter.ai/) - Unified access to 200+ AI models
- [GitHub Actions](https://github.com/features/actions)

## Migration from Gemini

If you're upgrading from the Gemini version (v2.x), just update your workflow:

**Old (Gemini):**
```yaml
- uses: vincetran/flutter-ai-review-bot@v2
  with:
    gemini-api-key: ${{ secrets.GEMINI_API_KEY }}
    github-token: ${{ secrets.GITHUB_TOKEN }}
```

**New (OpenRouter):**
```yaml
- uses: vincetran/flutter-ai-review-bot@main
  with:
    openrouter-api-key: ${{ secrets.OPENROUTER_API_KEY }}
    github-token: ${{ secrets.GITHUB_TOKEN }}
```

**Note**: Model selection is now controlled by project maintainers in `config.py`, not by workflow configuration. This ensures consistent review quality across all PRs.

