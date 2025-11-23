"""Configuration management for AI code reviewer.

Handles environment variables and constants used across the application.
"""

import os


class Config:
    """Configuration class for managing environment variables and constants."""

    # Environment variables
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")
    GITHUB_REF = os.getenv("GITHUB_REF", "")
    REVIEW_LANGUAGE = os.getenv("REVIEW_LANGUAGE", "vietnamese").lower()

    # Constants
    MAX_DIFF_LENGTH = 12000  # Limit diff size to avoid huge token payloads
    MAX_COMMENT_LENGTH = 60000  # GitHub has 65,536 char limit, use 60k for safety
    COMMENT_HEADER = "🤖 **AI Code Review - Flutter (Gemini)**\n\n"

    # Gemini model preferences (ordered by priority)
    # Flash models have higher quota (15 RPM) vs Pro models (2 RPM)
    PREFERRED_MODEL_PATTERNS = [
        'flash-latest',    # Best: gemini-flash-latest (15 RPM free tier)
        '2.5-flash',       # Good: gemini-2.5-flash
        '2.0-flash',       # Good: gemini-2.0-flash
        'flash',           # Any flash model
        'pro-latest',      # Lower priority: gemini-pro-latest (2 RPM only!)
        'pro',             # Fallback: any pro model
    ]

    # Fallback models if detection fails
    FALLBACK_MODELS = [
        'models/gemini-flash-latest',
        'models/gemini-2.5-flash',
        'models/gemini-2.0-flash',
        'models/gemini-pro-latest',
    ]

    # Models to exclude (special purpose models)
    EXCLUDED_MODEL_KEYWORDS = [
        'thinking', 'tts', 'image', 'gemma', 'learnlm'
    ]

    # Gemini generation settings
    GENERATION_CONFIG = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
    }

    # Retry configuration
    MAX_RETRIES = 2
    INITIAL_RETRY_DELAY = 5  # seconds
    RETRY_BACKOFF_MULTIPLIER = 2

    @classmethod
    def validate(cls) -> list[str]:
        """Validate required configuration.

        Returns:
            List of validation error messages. Empty if valid.
        """
        errors = []

        if not cls.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY is not set")

        if not cls.GITHUB_TOKEN:
            errors.append("GITHUB_TOKEN is not set")

        if not cls.GITHUB_REPOSITORY:
            errors.append("GITHUB_REPOSITORY is not set")

        if cls.REVIEW_LANGUAGE not in ['vietnamese', 'english']:
            errors.append(f"Invalid REVIEW_LANGUAGE: {cls.REVIEW_LANGUAGE}. Must be 'vietnamese' or 'english'")

        return errors

    @classmethod
    def print_debug_info(cls):
        """Print configuration for debugging (with masked secrets)."""
        print("=" * 60)
        print("🔍 Environment Variables Check:")
        print("=" * 60)
        print(f"   GITHUB_REF:        {cls.GITHUB_REF or '❌ NOT SET'}")
        print(f"   GITHUB_REPOSITORY: {cls.GITHUB_REPOSITORY or '❌ NOT SET'}")
        print(f"   GITHUB_TOKEN:      {'✅ SET (' + cls.GITHUB_TOKEN[:8] + '...)' if cls.GITHUB_TOKEN else '❌ NOT SET'}")
        print(f"   GEMINI_API_KEY:    {'✅ SET' if cls.GEMINI_API_KEY else '❌ NOT SET'}")
        print(f"   REVIEW_LANGUAGE:   {cls.REVIEW_LANGUAGE}")
        print("=" * 60)
        print()
