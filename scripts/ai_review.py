#!/usr/bin/env python3
"""AI reviewer script for GitHub Actions using Google Gemini (gemini-1.5-pro).

Behavior:
- Extracts the current PR number from GITHUB_REF
- Downloads the PR diff
- Sends a concise prompt to Gemini (gemini-1.5-pro) asking for a short, high-level review
- Posts one consolidated Markdown comment to the PR

Environment variables (provided via GitHub Actions secrets / env):
- GEMINI_API_KEY: API key for Google Generative AI (Gemini)
- GITHUB_TOKEN: GitHub token (usually provided by Actions)
- GITHUB_REPOSITORY: owner/repo
- GITHUB_REF: the Git ref (expects refs/pull/<PR>/merge or refs/pull/<PR>/head)
- GUIDE_FILE_PATH: (optional) custom path to coding guide file
- REVIEW_LANGUAGE: (optional) review language - 'vietnamese' or 'english' (default: vietnamese)

"""

import os
import sys
import requests  # pyright: ignore[reportMissingModuleSource]
import json
import textwrap
import time

# Try to import Google Generative AI SDK (if present)
try:
    import google.generativeai as genai  # pyright: ignore[reportMissingImports]
    has_gemini_sdk = True
except Exception:
    has_gemini_sdk = False

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = os.getenv("GITHUB_REPOSITORY")
GITHUB_REF = os.getenv("GITHUB_REF", "")
GUIDE_FILE_PATH = os.getenv("GUIDE_FILE_PATH", "")
REVIEW_LANGUAGE = os.getenv("REVIEW_LANGUAGE", "vietnamese").lower()

def get_pr_number_from_ref(ref: str):
    # expected formats:
    # refs/pull/<PR>/merge or refs/pull/<PR>/head
    parts = ref.split("/")
    if len(parts) >= 3 and parts[1] == "pull":
        return parts[2]
    return None

def fetch_pr_diff(repo: str, pr_number: str, token: str):
    pr_url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"

    print(f"   Fetching PR metadata from: {pr_url}")

    # First, get PR metadata with JSON
    headers_json = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    try:
        r = requests.get(pr_url, headers=headers_json, timeout=30)
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if r.status_code == 404:
            raise RuntimeError(
                f"PR #{pr_number} not found in {repo}.\n"
                f"   API URL: {pr_url}\n"
                f"   Check that:\n"
                f"   - PR exists and is open\n"
                f"   - GITHUB_TOKEN has correct permissions\n"
                f"   - Repository name is correct: {repo}"
            )
        elif r.status_code == 401:
            raise RuntimeError("Authentication failed. GITHUB_TOKEN may be invalid or expired.")
        else:
            raise RuntimeError(f"GitHub API error ({r.status_code}): {e}")

    pr_data = r.json()
    pr_state = pr_data.get("state", "unknown")
    pr_title = pr_data.get("title", "N/A")

    print(f"   ✅ PR found: '{pr_title}'")
    print(f"   State: {pr_state}")

    # Use GitHub API to get diff (more reliable for private repos)
    print(f"   Fetching diff via GitHub API...")
    headers_diff = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3.diff"}
    try:
        diff_resp = requests.get(pr_url, headers=headers_diff, timeout=30)
        diff_resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(
            f"Failed to fetch diff via API\n"
            f"   Status code: {diff_resp.status_code}\n"
            f"   Error: {e}\n"
            f"   This may happen if:\n"
            f"   - GITHUB_TOKEN lacks 'repo' scope for private repos\n"
            f"   - The PR has no changes\n"
            f"   - API rate limit exceeded"
        )

    diff_text = diff_resp.text
    if not diff_text or len(diff_text.strip()) == 0:
        raise RuntimeError("PR diff is empty. The PR may have no code changes.")

    print(f"   ✅ Diff fetched successfully ({len(diff_text)} characters)")
    return diff_text

def call_gemini(prompt: str) -> str:
    """Call Gemini API to generate code review"""
    if not GEMINI_KEY:
        raise RuntimeError("GEMINI_API_KEY not set")

    if not has_gemini_sdk:
        raise RuntimeError("google.generativeai SDK not installed. Please add it to requirements.txt")

    try:
        genai.configure(api_key=GEMINI_KEY)

        # List available models for debugging
        available_models = []
        try:
            print("   Listing available Gemini models...")
            for model in genai.list_models():
                if 'generateContent' in model.supported_generation_methods:
                    available_models.append(model.name)
                    print(f"      ✅ {model.name}")

            if not available_models:
                print("      ⚠️  No models with generateContent found!")
                raise RuntimeError("No Gemini models available. Check API key permissions.")
        except Exception as e:
            print(f"      ⚠️  Could not list models: {e}")
            # Continue with default models as fallback

        # Prefer FLASH models first (higher quota: 15 RPM vs 2 RPM for pro)
        # Priority: flash-latest > 2.5-flash > 2.0-flash > pro (fallback)
        preferred_patterns = [
            'flash-latest',        # Best: gemini-flash-latest (15 RPM free tier)
            '2.5-flash',           # Good: gemini-2.5-flash
            '2.0-flash',           # Good: gemini-2.0-flash
            'flash',               # Any flash model
            'pro-latest',          # Lower priority: gemini-pro-latest (2 RPM only!)
            'pro',                 # Fallback: any pro model
        ]

        # Build list of models to try based on what's actually available
        models_to_try = []
        if available_models:
            for pattern in preferred_patterns:
                for model in available_models:
                    model_lower = model.lower()
                    # Avoid duplicate and special models (thinking, tts, image, etc.)
                    if (pattern in model_lower and
                        model not in models_to_try and
                        'thinking' not in model_lower and
                        'tts' not in model_lower and
                        'image' not in model_lower and
                        'gemma' not in model_lower and
                        'learnlm' not in model_lower):
                        models_to_try.append(model)

        # Fallback to hardcoded list if no models detected
        if not models_to_try:
            print("   Using fallback model list...")
            models_to_try = [
                'models/gemini-flash-latest',
                'models/gemini-2.5-flash',
                'models/gemini-2.0-flash',
                'models/gemini-pro-latest',
            ]

        print(f"   Models to try (in order): {', '.join(models_to_try[:3])}...")

        # Configure generation settings
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,  # Increased to handle long reviews
        }

        last_error = None
        for model_name in models_to_try:
            try:
                print(f"   Trying Gemini model: {model_name}...")
                model = genai.GenerativeModel(model_name)

                # Retry logic for rate limit errors
                max_retries = 2
                retry_delay = 5  # Start with 5 seconds

                for attempt in range(max_retries + 1):
                    try:
                        if attempt > 0:
                            print(f"      Retry attempt {attempt}/{max_retries} after {retry_delay}s...")
                            time.sleep(retry_delay)

                        response = model.generate_content(
                            prompt,
                            generation_config=generation_config
                        )

                        # Extract text from response
                        if not response or not response.text:
                            print(f"   ⚠️  {model_name} returned empty response")
                            break  # Try next model

                        print(f"   ✅ Review generated with {model_name} ({len(response.text)} characters)")
                        return response.text

                    except Exception as retry_error:
                        retry_msg = str(retry_error)
                        # Handle quota/rate limit errors with retry
                        if "429" in retry_msg or "quota" in retry_msg.lower() or "rate" in retry_msg.lower():
                            if attempt < max_retries:
                                print(f"      ⚠️  Rate limit hit, retrying in {retry_delay}s...")
                                retry_delay *= 2  # Exponential backoff
                                continue
                            else:
                                print(f"   ⚠️  {model_name} quota exceeded after retries, trying next model...")
                                last_error = retry_error
                                break
                        else:
                            # Non-retryable error
                            raise

            except Exception as e:
                error_msg = str(e)
                if "404" in error_msg or "not found" in error_msg.lower():
                    print(f"   ⚠️  {model_name} not available, trying next model...")
                    last_error = e
                    continue
                elif "429" in error_msg or "quota" in error_msg.lower():
                    # Quota exceeded, try next model (flash has higher quota)
                    print(f"   ⚠️  {model_name} quota exceeded, trying next model...")
                    last_error = e
                    continue
                else:
                    # Other critical errors (API key invalid, etc.)
                    raise

        # If all models failed
        raise RuntimeError(f"All Gemini models failed. Last error: {last_error}")

    except Exception as e:
        # Provide more detailed error message
        error_msg = str(e)
        if "API key" in error_msg.lower() or "api_key" in error_msg.lower():
            raise RuntimeError(
                f"Invalid GEMINI_API_KEY.\n"
                f"   Get a new API key at: https://aistudio.google.com/app/apikey\n"
                f"   Update GitHub Secret: Settings → Secrets → GEMINI_API_KEY"
            )
        elif "quota" in error_msg.lower() or "rate" in error_msg.lower() or "RESOURCE_EXHAUSTED" in error_msg or "429" in error_msg:
            raise RuntimeError(
                f"Gemini API quota exceeded.\n"
                f"   Free tier: 2 requests/min for Pro models, 15 requests/min for Flash models\n"
                f"   Wait ~60 seconds and retry, or upgrade at: https://ai.google.dev/pricing\n"
                f"   Monitor usage: https://ai.dev/usage\n"
                f"   Error: {e}"
            )
        elif "PERMISSION_DENIED" in error_msg:
            raise RuntimeError(
                f"Permission denied.\n"
                f"   Check if your API key has Gemini API enabled\n"
                f"   Enable at: https://aistudio.google.com/app/apikey\n"
                f"   Error: {e}"
            )
        else:
            raise RuntimeError(f"Gemini API call failed: {e}")

def post_pr_comment(repo: str, pr_number: str, body: str, token: str):
    """Post a single comment to PR. GitHub has a 65,536 character limit per comment."""
    comments_url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    payload = {"body": body}
    r = requests.post(comments_url, headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()

def post_pr_comments_chunked(repo: str, pr_number: str, review_text: str, token: str):
    """Split long reviews into multiple comments if needed.

    GitHub comment limit: 65,536 characters
    We use 60,000 as safe limit to account for markdown formatting
    """
    MAX_COMMENT_LENGTH = 60000
    header = "🤖 **AI Code Review - Flutter (Gemini)**\n\n"

    # If review fits in one comment, post it directly
    if len(review_text) <= MAX_COMMENT_LENGTH - len(header):
        full_comment = header + review_text
        post_pr_comment(repo, pr_number, full_comment, token)
        print(f"   ✅ Posted 1 comment ({len(full_comment)} characters)")
        return

    # Split into chunks
    print(f"   ⚠️  Review is long ({len(review_text)} chars), splitting into multiple comments...")

    # Split by sections (look for heading markers or bullet points)
    # Try to split at logical boundaries: ## headings, 🔴, ⚠️, 💡
    chunks = []
    current_chunk = ""
    SAFE_LIMIT = MAX_COMMENT_LENGTH - len(header) - 500  # Extra buffer for part header

    for line in review_text.split('\n'):
        # Check if adding this line would exceed limit
        test_chunk = current_chunk + line + '\n'

        if len(current_chunk) > SAFE_LIMIT:
            # Current chunk is already too big, must split now
            if line.strip().startswith(('##', '###', '🔴', '⚠️', '💡', '✅', '---')):
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

    # Post chunks
    for i, chunk in enumerate(chunks, 1):
        part_header = f"{header}"
        if len(chunks) > 1:
            part_header += f"**Part {i}/{len(chunks)}**\n\n"

        comment_body = part_header + chunk
        post_pr_comment(repo, pr_number, comment_body, token)
        print(f"   ✅ Posted part {i}/{len(chunks)} ({len(comment_body)} characters)")

        # Small delay between comments to avoid rate limiting
        if i < len(chunks):
            time.sleep(1)

def load_prompt_template(language: str) -> str:
    """Load prompt template from file based on language."""
    script_dir = os.path.dirname(__file__)

    if language == "english":
        prompt_file = os.path.join(script_dir, "prompts", "review_prompt_en.txt")
    else:  # Vietnamese (default)
        prompt_file = os.path.join(script_dir, "prompts", "review_prompt_vi.txt")

    try:
        with open(prompt_file, "r", encoding="utf-8") as f:
            template = f.read()
        print(f"   ✅ Loaded prompt template: {prompt_file}")
        return template
    except Exception as e:
        print(f"⚠️ Warning: Could not load prompt file from {prompt_file}: {e}")
        # Fallback to hardcoded Vietnamese prompt
        return """Bạn là một senior Flutter/Dart engineer. Hãy review code changes dưới đây theo coding standards của dự án.

=== QUY TẮC & CHUẨN MỰC LẬP TRÌNH ===
{coding_rules}

=== NHIỆM VỤ CỦA BẠN ===
Hãy phân tích code diff và CHỈ liệt kê những vấn đề/vi phạm thực sự tìm thấy.

YÊU CẦU QUAN TRỌNG:
- Trả lời HOÀN TOÀN BẰNG TIẾNG VIỆT
- Format: Markdown với emoji (🔴 lỗi nghiêm trọng, ⚠️ cảnh báo, 💡 gợi ý)

=== CODE DIFF CẦN REVIEW ===
{code_diff}
"""

def build_prompt(diff_text: str) -> str:
    short_diff = diff_text[:12000]  # limit to avoid huge payloads in tokens

    # Load coding rules from FLUTTER_CODE_REVIEW_GUIDE.md
    # Use custom path if provided, otherwise use default path
    if GUIDE_FILE_PATH and os.path.isabs(GUIDE_FILE_PATH):
        guide_path = GUIDE_FILE_PATH
    elif GUIDE_FILE_PATH:
        # If relative path provided, resolve from action root
        guide_path = os.path.abspath(GUIDE_FILE_PATH)
    else:
        # Default to script directory
        guide_path = os.path.join(os.path.dirname(__file__), "FLUTTER_CODE_REVIEW_GUIDE.md")

    coding_rules = ""
    try:
        with open(guide_path, "r", encoding="utf-8") as f:
            coding_rules = f.read()
        print(f"   ✅ Loaded guide from: {guide_path}")
    except Exception as e:
        print(f"⚠️ Warning: Could not load guide file from {guide_path}: {e}")
        # Fallback to minimal rules if file not found
        coding_rules = textwrap.dedent("""
        ## Key Flutter Review Rules:
        - Clean Architecture: Domain must NOT import Data/Presentation layers
        - GetX: Use init: only at root widget, Get.find() in children
        - Assets: Use Assets.icons.iconBack (NOT hardcoded paths)
        - i18n: Use context.tr() (NOT hardcoded strings)
        - Error Handling: Return Either<Failure, T> in repositories
        """)

    # Load prompt template based on language
    prompt_template = load_prompt_template(REVIEW_LANGUAGE)

    # Replace placeholders in template
    prompt = prompt_template.format(
        coding_rules=coding_rules,
        code_diff=short_diff
    )

    return prompt

def main():
    # Debug: Print environment variables (masked for security)
    print("=" * 60)
    print("🔍 Environment Variables Check:")
    print("=" * 60)
    print(f"   GITHUB_REF:        {GITHUB_REF or '❌ NOT SET'}")
    print(f"   GITHUB_REPOSITORY: {REPO or '❌ NOT SET'}")
    print(f"   GITHUB_TOKEN:      {'✅ SET (' + GITHUB_TOKEN[:8] + '...)' if GITHUB_TOKEN else '❌ NOT SET'}")
    print(f"   GEMINI_API_KEY:    {'✅ SET' if GEMINI_KEY else '❌ NOT SET'}")
    print(f"   REVIEW_LANGUAGE:   {REVIEW_LANGUAGE}")
    print(f"   GUIDE_FILE_PATH:   {GUIDE_FILE_PATH or '(default)'}")
    print("=" * 60)
    print()

    pr_number = get_pr_number_from_ref(GITHUB_REF)
    if not pr_number:
        print("⚠️ Could not determine PR number from GITHUB_REF.")
        print(f"   Expected format: refs/pull/<NUMBER>/merge or refs/pull/<NUMBER>/head")
        print(f"   Got: '{GITHUB_REF}'")
        print("\n💡 This script is designed to run in GitHub Actions, not locally.")
        print("   To test locally, set environment variables:")
        print("   export GITHUB_REF='refs/pull/4/merge'")
        print("   export GITHUB_TOKEN='your_github_token'")
        print("   export GITHUB_REPOSITORY='owner/repo'")
        sys.exit(0)

    if not GITHUB_TOKEN:
        print("❌ GITHUB_TOKEN is required (automatically provided by GitHub Actions).")
        print("💡 If running locally, set: export GITHUB_TOKEN=your_token")
        sys.exit(1)
    if not REPO:
        print("❌ GITHUB_REPOSITORY not set.")
        print("💡 If running locally, set: export GITHUB_REPOSITORY=owner/repo")
        sys.exit(1)

    try:
        print(f"🔍 Fetching diff for PR #{pr_number}...")
        diff = fetch_pr_diff(REPO, pr_number, GITHUB_TOKEN)
    except Exception as e:
        print(f"❌ Failed to fetch PR diff: {e}")
        sys.exit(1)

    prompt = build_prompt(diff)

    try:
        print("💬 Sending prompt to Gemini (gemini-1.5-pro)...")
        review = call_gemini(prompt)
    except Exception as e:
        print(f"❌ Gemini call failed: {e}")
        # Post a helpful comment indicating Gemini couldn't be called
        if REVIEW_LANGUAGE == "english":
            fallback = ("⚠️ AI review could not be generated due to configuration or SDK error.\n\n"
                       "Please ensure GEMINI_API_KEY is set and google-generativeai is installed.\n")
        else:
            fallback = ("⚠️ AI review không thể tạo được do lỗi cấu hình hoặc SDK.\n\n"
                       "Đảm bảo GEMINI_API_KEY đã được set và google-generativeai đã được cài đặt.\n")
        try:
            post_pr_comment(REPO, pr_number, "🤖 **AI Code Review - Flutter (Gemini)**\n\n" + fallback, GITHUB_TOKEN)
        except Exception:
            pass
        sys.exit(1)

    try:
        print("✉️ Posting review comment(s) to PR...")
        post_pr_comments_chunked(REPO, pr_number, review.strip(), GITHUB_TOKEN)
        print("✅ Posted AI review comment(s) successfully.")
    except Exception as e:
        print(f"❌ Failed to post comment: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
