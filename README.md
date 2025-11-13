# Flutter AI Code Reviewer (Gemini)

Automated GitHub Pull Request reviewer for **Flutter/Dart** projects using **Google Gemini AI**.

This action reviews Flutter code based on Clean Architecture principles, GetX best practices, and comprehensive coding standards. It posts **one consolidated AI review comment** on each Pull Request with specific, actionable feedback.

## Features

- ✅ **Smart Model Selection**: Automatically chooses the best available Gemini model (prioritizes Flash models for higher quota)
- ✅ **Clean Architecture Review**: Validates layer dependencies and architectural patterns
- ✅ **GetX Best Practices**: Checks controller lifecycle and instance management
- ✅ **Type Safety**: Detects hardcoded assets and translation strings
- ✅ **Multi-language Support**: Review comments in Vietnamese or English
- ✅ **Customizable Guide**: Use your own coding standards guide
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
          # guide-file-path: 'docs/CODING_STANDARDS.md'  # Optional: custom guide file path
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
| `guide-file-path` | No | `scripts/FLUTTER_CODE_REVIEW_GUIDE.md` | Path to custom coding standards guide |

### Examples

#### English Reviews

```yaml
- uses: vincetran/flutter-ai-review-bot@main
  with:
    gemini-api-key: ${{ secrets.GEMINI_API_KEY }}
    github-token: ${{ secrets.GITHUB_TOKEN }}
    review-language: 'english'
```

#### Custom Coding Guide

```yaml
- uses: vincetran/flutter-ai-review-bot@main
  with:
    gemini-api-key: ${{ secrets.GEMINI_API_KEY }}
    github-token: ${{ secrets.GITHUB_TOKEN }}
    guide-file-path: 'docs/my-custom-guide.md'
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
│   ├── ai_review.py                    # Main Python script
│   ├── requirements.txt                # Python dependencies
│   ├── FLUTTER_CODE_REVIEW_GUIDE.md   # Coding standards guide
│   └── prompts/                        # AI prompt templates
│       ├── review_prompt_vi.txt        # Vietnamese prompt
│       ├── review_prompt_en.txt        # English prompt
│       └── README.md                   # Prompt documentation
└── README.md
```

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

### Customizing the Review Guide

Create your own coding standards guide in Markdown format:

1. Create a file (e.g., `docs/MY_GUIDE.md`)
2. Use it in your workflow:
   ```yaml
   guide-file-path: 'docs/MY_GUIDE.md'
   ```

See [scripts/FLUTTER_CODE_REVIEW_GUIDE.md](scripts/FLUTTER_CODE_REVIEW_GUIDE.md) for an example.

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

