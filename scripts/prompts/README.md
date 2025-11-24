# Review Prompt Templates

This directory contains AI review prompt templates for different languages.

## Files

- **`review_prompt_vi.txt`** - Vietnamese review prompt template
- **`review_prompt_en.txt`** - English review prompt template

## Template Variables

Each prompt template uses the following placeholders:

- `{coding_rules}` - Replaced with combined content from all rule files in `scripts/rule/` directory
- `{code_diff}` - Replaced with the actual code diff from the pull request

## How to Customize

1. **Edit existing templates**: Modify the `.txt` files directly to change the review instructions
2. **Add new language**: Create a new file like `review_prompt_ja.txt` and update `ai_review.py` to support it

## Template Structure

Each template should follow this structure:

```
[Role Definition]

=== CODING RULES & STANDARDS ===
{coding_rules}

=== YOUR TASK ===
[Instructions for what to review]

[Requirements and formatting guidelines]

[Example format with emojis]

=== CODE DIFF TO REVIEW ===
{code_diff}
```

## Example: Adding Japanese Support

1. Create `review_prompt_ja.txt`:
```
あなたはシニアFlutter/Dartエンジニアです。以下のコード変更をレビューしてください。

=== コーディング規約 ===
{coding_rules}

=== タスク ===
...

=== コードDIFF ===
{code_diff}
```

2. Update `ai_review.py`:
```python
def load_prompt_template(language: str) -> str:
    if language == "english":
        prompt_file = "review_prompt_en.txt"
    elif language == "japanese":
        prompt_file = "review_prompt_ja.txt"
    else:  # Vietnamese (default)
        prompt_file = "review_prompt_vi.txt"
    ...
```

## Benefits

- ✅ **Easy to read**: Plain text format without Python string escaping
- ✅ **Easy to edit**: No need to modify Python code to change prompts
- ✅ **Version control**: Track prompt changes separately from code logic
- ✅ **Collaboration**: Non-developers can update prompts
- ✅ **Testing**: Easy to compare different prompt versions
