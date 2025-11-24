"""AI Code Reviewer Package for Flutter/Dart projects using Google Gemini."""

__version__ = "1.0.0"

from .config import Config
from .github_client import GitHubClient, GitHubAPIError
from .gemini_client import GeminiClient, GeminiAPIError
from .prompt_builder import PromptBuilder
from .diff_chunker import DiffChunker, DiffChunk
from .utils import (
    get_pr_number_from_ref,
    format_validation_errors,
    create_fallback_comment,
    print_usage_instructions
)

__all__ = [
    "Config",
    "GitHubClient",
    "GitHubAPIError",
    "GeminiClient",
    "GeminiAPIError",
    "PromptBuilder",
    "DiffChunker",
    "DiffChunk",
    "get_pr_number_from_ref",
    "format_validation_errors",
    "create_fallback_comment",
    "print_usage_instructions",
]
