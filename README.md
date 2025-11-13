# flutter-ai-review-bot

Automated GitHub Pull Request reviewer for **Flutter/Dart** projects using **Google Gemini (gemini-1.5-pro)**.
This repo is a starter template: drop it into your GitHub repository, add the required secrets, and the Action will post **one consolidated AI review comment** on each Pull Request.

## Features
- Trigger on PR open / update / reopen
- Fetch PR diff and send a concise prompt to Gemini
- Post a single consolidated markdown comment highlighting main issues and suggestions
- Optimized for Flutter/Dart (short, high-level feedback)

## Setup
1. Fork or copy this repository to your GitHub account.
2. Go to **Settings → Secrets → Actions** and add:
   - `GEMINI_API_KEY` (your Google Generative AI key)
   - `GITHUB_TOKEN` (usually provided by Actions automatically; no action required in most cases)
3. Create a PR in the repo to trigger the workflow.

## Notes
- The script uses `google-generativeai` SDK. Make sure the Actions runner can install dependencies from `scripts/requirements.txt`.
- The included script posts a single consolidated comment (one comment per PR) to keep noise low.
- If you prefer inline comments per file, adapt `ai_review.py` to create multiple comments (one per file/line) — that will increase API calls.

## Files
- `.github/workflows/ai-review.yml` — GitHub Actions workflow
- `scripts/ai_review.py` — main review script
- `scripts/requirements.txt` — python deps

## Customize
- To change the model, edit `ai_review.py` and replace `models/gemini-1.5-pro` with the desired model name.
- Adjust `prompt` in `ai_review.py` to tune the style/length of reviews.

