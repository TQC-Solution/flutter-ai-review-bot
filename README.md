# Flutter AI Code Reviewer (Gemini)

> **🎉 NEW: v2.0 - Refactored Architecture!** The codebase has been restructured from a monolithic 486-line script into 6 specialized modules for better maintainability and extensibility. See [Architecture](#architecture-refactored-v20) and [Refactoring Guide](REFACTORING.md) for details.

Automated GitHub Pull Request reviewer for **Flutter/Dart** projects using **Google Gemini AI**.

This action reviews Flutter code based on Clean Architecture principles, GetX best practices, and comprehensive coding standards. It posts **one consolidated AI review comment** on each Pull Request with specific, actionable feedback.

## Features

- ✅ **Smart Model Selection**: Automatically chooses the best available Gemini model (prioritizes Flash models for higher quota)
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

      - name: Run Gemini AI Code Reviewer
        uses: vincetran/flutter-ai-review-bot@main  # Or use a specific version tag
        with:
          gemini-api-key: ${{ secrets.GEMINI_API_KEY }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
          review-language: 'vietnamese'  # Optional: 'vietnamese' or 'english' (default: vietnamese)
```

### Setup

1. **Get a Gemini API Key**
   - Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Create a new API key

2. **Add GitHub Secret**
   - Go to your repository **Settings → Secrets and variables → Actions**
   - Click **New repository secret**
   - Name: `GEMINI_API_KEY`
   - Value: Your Gemini API key from step 1

3. **Create a Pull Request**
   - The action will automatically run and post a review comment

## Configuration Options

### Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `gemini-api-key` | Yes | - | Google Gemini API key for AI code review |
| `github-token` | Yes | - | GitHub token (use `${{ secrets.GITHUB_TOKEN }}`) |
| `review-language` | No | `vietnamese` | Review comment language: `vietnamese` or `english` |

### Examples

#### English Reviews

```yaml
- uses: vincetran/flutter-ai-review-bot@main
  with:
    gemini-api-key: ${{ secrets.GEMINI_API_KEY }}
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
│   ├── ai_review.py                    # Main orchestrator (104 lines)
│   ├── reviewer/                       # Modular package
│   │   ├── __init__.py                # Package exports
│   │   ├── config.py                  # Configuration management
│   │   ├── github_client.py           # GitHub API operations
│   │   ├── gemini_client.py           # Gemini AI integration
│   │   ├── prompt_builder.py          # Prompt construction
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
1. **[config.py](scripts/reviewer/config.py)** (98 lines)
   - Environment variables management
   - Configuration validation
   - Constants definition

2. **[github_client.py](scripts/reviewer/github_client.py)** (223 lines)
   - Fetch PR metadata and diffs
   - Post review comments
   - Handle long reviews with chunking

3. **[gemini_client.py](scripts/reviewer/gemini_client.py)** (247 lines)
   - Model selection and fallback
   - API calls with retry logic
   - Rate limit handling

4. **[prompt_builder.py](scripts/reviewer/prompt_builder.py)** (147 lines)
   - Load language-specific templates
   - Load coding guidelines
   - Build complete prompts

5. **[utils.py](scripts/reviewer/utils.py)** (88 lines)
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
export GEMINI_API_KEY='your_gemini_api_key'
export REVIEW_LANGUAGE='vietnamese'

# Install dependencies
pip install -r scripts/requirements.txt

# Run the script
python scripts/ai_review.py
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

## API Quotas

**Gemini Free Tier Limits:**
- Flash models: 15 requests/minute
- Pro models: 2 requests/minute

The action automatically:
- Prioritizes Flash models for higher quota
- Retries with exponential backoff on rate limits
- Falls back to alternative models if quota exceeded

To check your usage: [Google AI Studio Usage Dashboard](https://ai.google.dev/usage)

## Troubleshooting

### "GEMINI_API_KEY not set"
- Make sure you added the secret in repository Settings → Secrets

### "PR diff is empty"
- The PR has no code changes to review

### "Quota exceeded"
- Wait 60 seconds and retry
- Consider upgrading your Gemini API plan

### "Permission denied"
- Ensure your API key has Gemini API enabled at [Google AI Studio](https://aistudio.google.com/app/apikey)

## License

MIT License - Feel free to use and modify for your projects

## Contributing

Contributions welcome! Please open an issue or PR.

## Credits

Built with:
- [Google Generative AI SDK](https://github.com/google/generative-ai-python)
- [GitHub Actions](https://github.com/features/actions)

