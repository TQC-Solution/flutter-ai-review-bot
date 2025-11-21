"""GitHub API client for fetching PR information and posting comments.

Handles all interactions with GitHub API including:
- Fetching PR metadata
- Downloading PR diffs
- Posting review comments (with chunking for long reviews)
"""

import time
import requests  # pyright: ignore[reportMissingModuleSource]

from .config import Config


class GitHubAPIError(Exception):
    """Custom exception for GitHub API errors."""
    pass


class GitHubClient:
    """Client for interacting with GitHub API."""

    def __init__(self, repo: str, token: str):
        """Initialize GitHub client.

        Args:
            repo: Repository in format 'owner/repo'
            token: GitHub authentication token
        """
        self.repo = repo
        self.token = token
        self.base_url = f"https://api.github.com/repos/{repo}"

    def fetch_pr_diff(self, pr_number: str) -> str:
        """Fetch the diff for a pull request.

        Args:
            pr_number: Pull request number

        Returns:
            The PR diff as a string

        Raises:
            GitHubAPIError: If fetching fails
        """
        pr_url = f"{self.base_url}/pulls/{pr_number}"
        print(f"   Fetching PR metadata from: {pr_url}")

        # First, get PR metadata with JSON
        headers_json = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

        try:
            response = requests.get(pr_url, headers=headers_json, timeout=30)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                raise GitHubAPIError(
                    f"PR #{pr_number} not found in {self.repo}.\n"
                    f"   API URL: {pr_url}\n"
                    f"   Check that:\n"
                    f"   - PR exists and is open\n"
                    f"   - GITHUB_TOKEN has correct permissions\n"
                    f"   - Repository name is correct: {self.repo}"
                )
            elif response.status_code == 401:
                raise GitHubAPIError(
                    "Authentication failed. GITHUB_TOKEN may be invalid or expired."
                )
            else:
                raise GitHubAPIError(f"GitHub API error ({response.status_code}): {e}")

        pr_data = response.json()
        pr_state = pr_data.get("state", "unknown")
        pr_title = pr_data.get("title", "N/A")

        print(f"   ✅ PR found: '{pr_title}'")
        print(f"   State: {pr_state}")

        # Fetch diff via GitHub API (more reliable for private repos)
        print(f"   Fetching diff via GitHub API...")
        headers_diff = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3.diff"
        }

        try:
            diff_response = requests.get(pr_url, headers=headers_diff, timeout=30)
            diff_response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise GitHubAPIError(
                f"Failed to fetch diff via API\n"
                f"   Status code: {diff_response.status_code}\n"
                f"   Error: {e}\n"
                f"   This may happen if:\n"
                f"   - GITHUB_TOKEN lacks 'repo' scope for private repos\n"
                f"   - The PR has no changes\n"
                f"   - API rate limit exceeded"
            )

        diff_text = diff_response.text
        if not diff_text or len(diff_text.strip()) == 0:
            raise GitHubAPIError(
                "PR diff is empty. The PR may have no code changes."
            )

        print(f"   ✅ Diff fetched successfully ({len(diff_text)} characters)")
        return diff_text

    def post_comment(self, pr_number: str, body: str) -> dict:
        """Post a single comment to a PR.

        Args:
            pr_number: Pull request number
            body: Comment body (max 65,536 characters)

        Returns:
            API response JSON

        Raises:
            GitHubAPIError: If posting fails
        """
        comments_url = f"{self.base_url}/issues/{pr_number}/comments"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        payload = {"body": body}

        try:
            response = requests.post(
                comments_url, headers=headers, json=payload, timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            raise GitHubAPIError(f"Failed to post comment: {e}")

    def post_review_chunked(self, pr_number: str, review_text: str):
        """Post a code review, splitting into multiple comments if needed.

        GitHub has a 65,536 character limit per comment. This method
        automatically chunks long reviews into multiple comments.

        Args:
            pr_number: Pull request number
            review_text: Review text to post
        """
        header = Config.COMMENT_HEADER
        max_length = Config.MAX_COMMENT_LENGTH

        # If review fits in one comment, post it directly
        if len(review_text) <= max_length - len(header):
            full_comment = header + review_text
            self.post_comment(pr_number, full_comment)
            print(f"   ✅ Posted 1 comment ({len(full_comment)} characters)")
            return

        # Split into chunks
        print(
            f"   ⚠️  Review is long ({len(review_text)} chars), "
            f"splitting into multiple comments..."
        )

        chunks = self._split_review_into_chunks(review_text, max_length - len(header) - 500)

        # Post chunks
        for i, chunk in enumerate(chunks, 1):
            part_header = header
            if len(chunks) > 1:
                part_header += f"**Part {i}/{len(chunks)}**\n\n"

            comment_body = part_header + chunk
            self.post_comment(pr_number, comment_body)
            print(f"   ✅ Posted part {i}/{len(chunks)} ({len(comment_body)} characters)")

            # Small delay between comments to avoid rate limiting
            if i < len(chunks):
                time.sleep(1)

    def _split_review_into_chunks(self, text: str, safe_limit: int) -> list[str]:
        """Split review text into chunks at logical boundaries.

        Tries to split at markdown headings and emoji markers for better readability.

        Args:
            text: Text to split
            safe_limit: Maximum characters per chunk

        Returns:
            List of text chunks
        """
        chunks = []
        current_chunk = ""

        # Split boundary markers (headings, emoji sections)
        boundary_markers = ('##', '###', '🔴', '⚠️', '💡', '✅', '---')

        for line in text.split('\n'):
            test_chunk = current_chunk + line + '\n'

            if len(current_chunk) > safe_limit:
                # Current chunk is already too big, must split now
                if line.strip().startswith(boundary_markers):
                    # Good place to split - save current chunk
                    if current_chunk.strip():
                        chunks.append(current_chunk.strip())
                    current_chunk = line + '\n'
                elif current_chunk.strip():
                    # Force split even if not ideal boundary
                    chunks.append(current_chunk.strip())
                    current_chunk = line + '\n'
            else:
                # Still within limit, keep adding
                current_chunk = test_chunk

        # Add last chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks
