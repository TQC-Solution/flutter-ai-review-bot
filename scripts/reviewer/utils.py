"""Utility functions for AI code reviewer.

Contains helper functions for:
- Parsing GitHub references
- Validation
- Formatting
"""


def get_pr_number_from_ref(ref: str) -> str | None:
    """Extract PR number from GitHub ref.

    Args:
        ref: GitHub ref string (e.g., 'refs/pull/123/merge')

    Returns:
        PR number as string, or None if not found

    Examples:
        >>> get_pr_number_from_ref('refs/pull/123/merge')
        '123'
        >>> get_pr_number_from_ref('refs/pull/456/head')
        '456'
        >>> get_pr_number_from_ref('refs/heads/main')
        None
    """
    # Expected formats:
    # refs/pull/<PR>/merge or refs/pull/<PR>/head
    parts = ref.split("/")
    if len(parts) >= 3 and parts[1] == "pull":
        return parts[2]
    return None


def format_validation_errors(errors: list[str]) -> str:
    """Format validation errors into a readable message.

    Args:
        errors: List of error messages

    Returns:
        Formatted error string
    """
    if not errors:
        return ""

    error_list = "\n".join(f"   - {error}" for error in errors)
    return f"❌ Configuration validation failed:\n{error_list}"


def create_fallback_comment(language: str, error_message: str) -> str:
    """Create a fallback comment when review generation fails.

    Args:
        language: 'english' or 'vietnamese'
        error_message: The error message to include

    Returns:
        Formatted fallback comment
    """
    if language == "english":
        return (
            "⚠️ AI review could not be generated due to configuration or API error.\n\n"
            "Please ensure OPENROUTER_API_KEY is set correctly.\n\n"
            f"Error details:\n```\n{error_message}\n```"
        )
    else:
        return (
            "⚠️ AI review không thể tạo được do lỗi cấu hình hoặc API.\n\n"
            "Đảm bảo OPENROUTER_API_KEY đã được set đúng.\n\n"
            f"Chi tiết lỗi:\n```\n{error_message}\n```"
        )


def print_usage_instructions(ref: str):
    """Print instructions for running the script.

    Args:
        ref: The GITHUB_REF value that was provided
    """
    print("⚠️ Could not determine PR number from GITHUB_REF.")
    print(f"   Expected format: refs/pull/<NUMBER>/merge or refs/pull/<NUMBER>/head")
    print(f"   Got: '{ref}'")
    print("\n💡 This script is designed to run in GitHub Actions, not locally.")
    print("   To test locally, set environment variables:")
    print("   export GITHUB_REF='refs/pull/4/merge'")
    print("   export GITHUB_TOKEN='your_github_token'")
    print("   export GITHUB_REPOSITORY='owner/repo'")
