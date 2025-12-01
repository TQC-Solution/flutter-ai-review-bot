"""AI Code Reviewer Package for Flutter/Dart projects using OpenRouter AI."""

__version__ = "3.0.0"

from .config import Config
from .github_client import GitHubClient, GitHubAPIError
from .openrouter_client import OpenRouterClient, OpenRouterAPIError
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
    "OpenRouterClient",
    "OpenRouterAPIError",
    "PromptBuilder",
    "DiffChunker",
    "DiffChunk",
    "get_pr_number_from_ref",
    "format_validation_errors",
    "create_fallback_comment",
    "print_usage_instructions",
]
