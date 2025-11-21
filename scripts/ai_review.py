#!/usr/bin/env python3
"""AI reviewer script for GitHub Actions using Google Gemini.

This is the main orchestrator that coordinates all components:
- Configuration validation
- GitHub PR fetching
- Prompt building
- AI review generation
- Comment posting

For detailed implementation, see the reviewer package modules:
- config.py: Configuration and environment variables
- github_client.py: GitHub API operations
- gemini_client.py: Gemini AI integration
- prompt_builder.py: Prompt construction
- utils.py: Helper functions
"""

import sys

from reviewer.config import Config
from reviewer.github_client import GitHubClient, GitHubAPIError
from reviewer.gemini_client import GeminiClient, GeminiAPIError
from reviewer.prompt_builder import PromptBuilder
from reviewer.utils import (
    get_pr_number_from_ref,
    format_validation_errors,
    create_fallback_comment,
    print_usage_instructions
)


def main():
    """Main entry point for AI code review workflow."""

    # Print environment configuration for debugging
    Config.print_debug_info()

    # Validate configuration
    validation_errors = Config.validate()
    if validation_errors:
        # Some errors are acceptable for local testing (missing GitHub ref)
        critical_errors = [e for e in validation_errors if "GITHUB_REF" not in e]
        if critical_errors:
            print(format_validation_errors(critical_errors))
            sys.exit(1)

    # Extract PR number from GitHub ref
    pr_number = get_pr_number_from_ref(Config.GITHUB_REF)
    if not pr_number:
        print_usage_instructions(Config.GITHUB_REF)
        sys.exit(0)

    # Initialize clients
    github_client = GitHubClient(Config.GITHUB_REPOSITORY, Config.GITHUB_TOKEN)
    gemini_client = GeminiClient(Config.GEMINI_API_KEY)
    prompt_builder = PromptBuilder(Config.REVIEW_LANGUAGE)

    # Step 1: Fetch PR diff
    try:
        print(f"🔍 Fetching diff for PR #{pr_number}...")
        diff = github_client.fetch_pr_diff(pr_number)
    except GitHubAPIError as e:
        print(f"❌ Failed to fetch PR diff: {e}")
        sys.exit(1)

    # Step 2: Build review prompt
    print("📝 Building review prompt...")
    prompt = prompt_builder.build_prompt(diff)

    # Step 3: Generate AI review
    try:
        print("💬 Sending prompt to Gemini AI...")
        review = gemini_client.generate_review(prompt)
    except GeminiAPIError as e:
        print(f"❌ Gemini call failed: {e}")

        # Post a helpful fallback comment
        fallback_comment = create_fallback_comment(
            Config.REVIEW_LANGUAGE,
            str(e)
        )
        try:
            github_client.post_comment(
                pr_number,
                Config.COMMENT_HEADER + fallback_comment
            )
        except Exception:
            pass  # Silently fail if we can't post error comment

        sys.exit(1)

    # Step 4: Post review to PR
    try:
        print("✉️ Posting review comment(s) to PR...")
        github_client.post_review_chunked(pr_number, review.strip())
        print("✅ Posted AI review comment(s) successfully.")
    except GitHubAPIError as e:
        print(f"❌ Failed to post comment: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
