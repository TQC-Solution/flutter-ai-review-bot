"""Google Gemini AI client for code review generation.

Handles all interactions with Google Gemini API including:
- Model selection and fallback
- API call with retry logic
- Error handling and informative error messages
"""

import time

try:
    import google.generativeai as genai  # pyright: ignore[reportMissingImports]
    HAS_GEMINI_SDK = True
except Exception:
    HAS_GEMINI_SDK = False

from .config import Config


class GeminiAPIError(Exception):
    """Custom exception for Gemini API errors."""
    pass


class GeminiClient:
    """Client for interacting with Google Gemini API."""

    def __init__(self, api_key: str):
        """Initialize Gemini client.

        Args:
            api_key: Google Gemini API key

        Raises:
            GeminiAPIError: If SDK is not installed
        """
        if not api_key:
            raise GeminiAPIError("GEMINI_API_KEY not set")

        if not HAS_GEMINI_SDK:
            raise GeminiAPIError(
                "google.generativeai SDK not installed. "
                "Please add it to requirements.txt"
            )

        self.api_key = api_key
        genai.configure(api_key=api_key)

    def generate_review(self, prompt: str) -> str:
        """Generate code review using Gemini AI.

        Tries multiple models in order of preference (flash models first for higher quota).
        Implements retry logic for rate limit errors.

        Args:
            prompt: The review prompt including code diff

        Returns:
            Generated review text

        Raises:
            GeminiAPIError: If all models fail or API error occurs
        """
        available_models = self._list_available_models()
        models_to_try = self._select_models_to_try(available_models)

        print(f"   Models to try (in order): {', '.join(models_to_try[:3])}...")

        last_error = None
        for model_name in models_to_try:
            try:
                review = self._try_model_with_retry(model_name, prompt)
                if review:
                    return review
            except Exception as e:
                last_error = e
                error_msg = str(e)

                # Handle different error types
                if "404" in error_msg or "not found" in error_msg.lower():
                    print(f"   ⚠️  {model_name} not available, trying next model...")
                    continue
                elif "429" in error_msg or "quota" in error_msg.lower():
                    print(f"   ⚠️  {model_name} quota exceeded, trying next model...")
                    continue
                else:
                    # Critical errors (invalid API key, etc.)
                    raise self._create_detailed_error(e)

        # If all models failed
        raise GeminiAPIError(f"All Gemini models failed. Last error: {last_error}")

    def _list_available_models(self) -> list[str]:
        """List available Gemini models with generateContent capability.

        Returns:
            List of available model names
        """
        available_models = []

        try:
            print("   Listing available Gemini models...")
            for model in genai.list_models():
                if 'generateContent' in model.supported_generation_methods:
                    available_models.append(model.name)
                    print(f"      ✅ {model.name}")

            if not available_models:
                print("      ⚠️  No models with generateContent found!")
        except Exception as e:
            print(f"      ⚠️  Could not list models: {e}")

        return available_models

    def _select_models_to_try(self, available_models: list[str]) -> list[str]:
        """Select models to try based on availability and preferences.

        Prioritizes flash models (higher quota) over pro models.

        Args:
            available_models: List of available model names

        Returns:
            Ordered list of model names to try
        """
        models_to_try = []

        if available_models:
            # Build list based on available models and preferences
            for pattern in Config.PREFERRED_MODEL_PATTERNS:
                for model in available_models:
                    model_lower = model.lower()

                    # Check if model matches pattern and isn't excluded
                    if (pattern in model_lower and
                        model not in models_to_try and
                        not any(excluded in model_lower
                               for excluded in Config.EXCLUDED_MODEL_KEYWORDS)):
                        models_to_try.append(model)

        # Fallback to hardcoded list if no models detected
        if not models_to_try:
            print("   Using fallback model list...")
            models_to_try = Config.FALLBACK_MODELS

        return models_to_try

    def _try_model_with_retry(self, model_name: str, prompt: str) -> str | None:
        """Try a specific model with retry logic for rate limits.

        Args:
            model_name: Name of the Gemini model to use
            prompt: The review prompt

        Returns:
            Generated text or None if model returns empty response

        Raises:
            Exception: If non-retryable error occurs or max retries exceeded
        """
        print(f"   Trying Gemini model: {model_name}...")
        model = genai.GenerativeModel(model_name)

        retry_delay = Config.INITIAL_RETRY_DELAY

        for attempt in range(Config.MAX_RETRIES + 1):
            try:
                if attempt > 0:
                    print(f"      Retry attempt {attempt}/{Config.MAX_RETRIES} "
                          f"after {retry_delay}s...")
                    time.sleep(retry_delay)

                response = model.generate_content(
                    prompt,
                    generation_config=Config.GENERATION_CONFIG
                )

                # Check if response is valid
                if not response or not response.text:
                    print(f"   ⚠️  {model_name} returned empty response")
                    return None

                print(f"   ✅ Review generated with {model_name} "
                      f"({len(response.text)} characters)")
                return response.text

            except Exception as retry_error:
                retry_msg = str(retry_error)

                # Handle quota/rate limit errors with retry
                if ("429" in retry_msg or
                    "quota" in retry_msg.lower() or
                    "rate" in retry_msg.lower()):

                    if attempt < Config.MAX_RETRIES:
                        print(f"      ⚠️  Rate limit hit, retrying in {retry_delay}s...")
                        retry_delay *= Config.RETRY_BACKOFF_MULTIPLIER
                        continue
                    else:
                        print(f"   ⚠️  {model_name} quota exceeded after retries, "
                              f"trying next model...")
                        raise
                else:
                    # Non-retryable error
                    raise

        return None

    def _create_detailed_error(self, error: Exception) -> GeminiAPIError:
        """Create a detailed error message based on the error type.

        Args:
            error: The original exception

        Returns:
            GeminiAPIError with detailed message
        """
        error_msg = str(error)

        if "API key" in error_msg.lower() or "api_key" in error_msg.lower():
            return GeminiAPIError(
                f"Invalid GEMINI_API_KEY.\n"
                f"   Get a new API key at: https://aistudio.google.com/app/apikey\n"
                f"   Update GitHub Secret: Settings → Secrets → GEMINI_API_KEY"
            )
        elif ("quota" in error_msg.lower() or
              "rate" in error_msg.lower() or
              "RESOURCE_EXHAUSTED" in error_msg or
              "429" in error_msg):
            return GeminiAPIError(
                f"Gemini API quota exceeded.\n"
                f"   Free tier: 2 requests/min for Pro models, "
                f"15 requests/min for Flash models\n"
                f"   Wait ~60 seconds and retry, or upgrade at: "
                f"https://ai.google.dev/pricing\n"
                f"   Monitor usage: https://ai.dev/usage\n"
                f"   Error: {error}"
            )
        elif "PERMISSION_DENIED" in error_msg:
            return GeminiAPIError(
                f"Permission denied.\n"
                f"   Check if your API key has Gemini API enabled\n"
                f"   Enable at: https://aistudio.google.com/app/apikey\n"
                f"   Error: {error}"
            )
        else:
            return GeminiAPIError(f"Gemini API call failed: {error}")
