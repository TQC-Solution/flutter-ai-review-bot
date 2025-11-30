"""OpenRouter AI client for code review generation.

Handles all interactions with OpenRouter API including:
- Model selection and configuration
- API call with retry logic
- Error handling and informative error messages
- Support for reasoning-enabled models
"""

from __future__ import annotations

import time
import json
import requests

from .config import Config


class OpenRouterAPIError(Exception):
    """Custom exception for OpenRouter API errors."""
    pass


class OpenRouterClient:
    """Client for interacting with OpenRouter API."""

    def __init__(self, api_key: str):
        """Initialize OpenRouter client.

        Args:
            api_key: OpenRouter API key

        Raises:
            OpenRouterAPIError: If API key is not set
        """
        if not api_key:
            raise OpenRouterAPIError("OPENROUTER_API_KEY not set")

        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def generate_review(self, prompt: str) -> str:
        """Generate code review using OpenRouter AI.

        Tries the configured model with retry logic for rate limit errors.

        Args:
            prompt: The review prompt including code diff

        Returns:
            Generated review text

        Raises:
            OpenRouterAPIError: If API call fails
        """
        model_name = Config.OPENROUTER_MODEL
        print(f"   Using OpenRouter model: {model_name}")

        try:
            review = self._try_model_with_retry(model_name, prompt)
            if review:
                return review
            else:
                raise OpenRouterAPIError(f"Model {model_name} returned empty response")
        except Exception as e:
            raise self._create_detailed_error(e)

    def _try_model_with_retry(self, model_name: str, prompt: str) -> str | None:
        """Try a specific model with retry logic for rate limits.

        Args:
            model_name: Name of the OpenRouter model to use
            prompt: The review prompt

        Returns:
            Generated text or None if model returns empty response

        Raises:
            Exception: If non-retryable error occurs or max retries exceeded
        """
        print(f"   Calling OpenRouter API with model: {model_name}...")

        retry_delay = Config.INITIAL_RETRY_DELAY

        for attempt in range(Config.MAX_RETRIES + 1):
            try:
                if attempt > 0:
                    print(f"      Retry attempt {attempt}/{Config.MAX_RETRIES} "
                          f"after {retry_delay}s...")
                    time.sleep(retry_delay)

                # Build request payload
                payload = {
                    "model": model_name,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                }

                # Add generation config
                if Config.GENERATION_CONFIG:
                    if not isinstance(Config.GENERATION_CONFIG, dict):
                        raise OpenRouterAPIError(
                            f"GENERATION_CONFIG must be a dict, got {type(Config.GENERATION_CONFIG).__name__}"
                        )
                    if "temperature" in Config.GENERATION_CONFIG:
                        payload["temperature"] = Config.GENERATION_CONFIG["temperature"]
                    if "top_p" in Config.GENERATION_CONFIG:
                        payload["top_p"] = Config.GENERATION_CONFIG["top_p"]
                    if "max_output_tokens" in Config.GENERATION_CONFIG:
                        payload["max_tokens"] = Config.GENERATION_CONFIG["max_output_tokens"]

                # Enable reasoning if supported by model
                if Config.ENABLE_REASONING:
                    payload["reasoning"] = {"enabled": True}

                # Make API call
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    data=json.dumps(payload),
                    timeout=120  # 2 minute timeout
                )

                # Check for HTTP errors
                if response.status_code == 429:
                    # Rate limit error - retry
                    if attempt < Config.MAX_RETRIES:
                        print(f"      ⚠️  Rate limit hit (429), retrying in {retry_delay}s...")
                        retry_delay *= Config.RETRY_BACKOFF_MULTIPLIER
                        continue
                    else:
                        raise OpenRouterAPIError(
                            f"Rate limit exceeded after {Config.MAX_RETRIES} retries. "
                            f"Response: {response.text}"
                        )

                if response.status_code == 401:
                    raise OpenRouterAPIError(
                        "Invalid API key (401). "
                        "Get a new API key at: https://openrouter.ai/keys"
                    )

                if response.status_code == 402:
                    raise OpenRouterAPIError(
                        "Insufficient credits (402). "
                        "Add credits at: https://openrouter.ai/credits"
                    )

                if response.status_code == 403:
                    raise OpenRouterAPIError(
                        "Access forbidden (403). "
                        "Check your API key permissions."
                    )

                if response.status_code != 200:
                    raise OpenRouterAPIError(
                        f"API call failed with status {response.status_code}: {response.text}"
                    )

                # Parse response
                response_data = response.json()

                # Debug logging
                print(f"   DEBUG: Response type: {type(response_data).__name__}")

                # Validate response_data is a dict
                if not isinstance(response_data, dict):
                    raise OpenRouterAPIError(
                        f"Invalid API response format: expected dict, got {type(response_data).__name__}. "
                        f"Response: {response_data}"
                    )

                if "error" in response_data:
                    error_data = response_data["error"]
                    # Handle different error formats: dict, list, or string
                    if isinstance(error_data, dict):
                        error_msg = error_data.get("message", str(error_data))
                    elif isinstance(error_data, list):
                        # If error is a list, convert to string representation
                        error_msg = "; ".join(str(e) for e in error_data)
                    else:
                        error_msg = str(error_data)
                    raise OpenRouterAPIError(f"API error: {error_msg}")

                # Extract content from response
                if "choices" not in response_data or len(response_data["choices"]) == 0:
                    print(f"   ⚠️  {model_name} returned no choices")
                    return None

                # Debug logging
                print(f"   DEBUG: Choices type: {type(response_data['choices']).__name__}")
                print(f"   DEBUG: First choice type: {type(response_data['choices'][0]).__name__}")

                # Get first choice - handle both dict and list formats
                first_choice = response_data["choices"][0]
                if not isinstance(first_choice, dict):
                    raise OpenRouterAPIError(
                        f"Unexpected response format: choices[0] is {type(first_choice).__name__}, "
                        f"expected dict. Response: {response_data}"
                    )

                message = first_choice.get("message", {})
                if not isinstance(message, dict):
                    raise OpenRouterAPIError(
                        f"Unexpected message format: message is {type(message).__name__}, "
                        f"expected dict. Response: {response_data}"
                    )

                content = message.get("content", "")

                if not content:
                    print(f"   ⚠️  {model_name} returned empty content")
                    return None

                print(f"   ✅ Review generated with {model_name} "
                      f"({len(content)} characters)")

                # Log reasoning details if available
                if "reasoning_details" in message:
                    reasoning_details = message["reasoning_details"]
                    if isinstance(reasoning_details, dict):
                        print(f"   🧠 Reasoning tokens used: "
                              f"{reasoning_details.get('tokens', 'N/A')}")
                    else:
                        print(f"   🧠 Reasoning details: {reasoning_details}")

                return content

            except requests.exceptions.Timeout:
                if attempt < Config.MAX_RETRIES:
                    print(f"      ⚠️  Request timeout, retrying in {retry_delay}s...")
                    retry_delay *= Config.RETRY_BACKOFF_MULTIPLIER
                    continue
                else:
                    raise OpenRouterAPIError(
                        f"Request timeout after {Config.MAX_RETRIES} retries"
                    )

            except requests.exceptions.RequestException as e:
                # Network errors
                if attempt < Config.MAX_RETRIES:
                    print(f"      ⚠️  Network error: {e}, retrying in {retry_delay}s...")
                    retry_delay *= Config.RETRY_BACKOFF_MULTIPLIER
                    continue
                else:
                    raise OpenRouterAPIError(
                        f"Network error after {Config.MAX_RETRIES} retries: {e}"
                    )

            except OpenRouterAPIError:
                # Re-raise our custom errors
                raise

            except Exception as e:
                # Other errors
                raise OpenRouterAPIError(f"Unexpected error: {e}")

        return None

    def _create_detailed_error(self, error: Exception) -> OpenRouterAPIError:
        """Create a detailed error message based on the error type.

        Args:
            error: The original exception

        Returns:
            OpenRouterAPIError with detailed message
        """
        if isinstance(error, OpenRouterAPIError):
            return error

        error_msg = str(error)

        if "api key" in error_msg.lower() or "401" in error_msg:
            return OpenRouterAPIError(
                f"Invalid OPENROUTER_API_KEY.\n"
                f"   Get a new API key at: https://openrouter.ai/keys\n"
                f"   Update GitHub Secret: Settings → Secrets → OPENROUTER_API_KEY"
            )
        elif "rate" in error_msg.lower() or "429" in error_msg:
            return OpenRouterAPIError(
                f"OpenRouter API rate limit exceeded.\n"
                f"   Check your rate limits at: https://openrouter.ai/settings/limits\n"
                f"   Wait and retry, or upgrade your plan\n"
                f"   Error: {error}"
            )
        elif "credits" in error_msg.lower() or "402" in error_msg:
            return OpenRouterAPIError(
                f"Insufficient OpenRouter credits.\n"
                f"   Add credits at: https://openrouter.ai/credits\n"
                f"   Error: {error}"
            )
        else:
            return OpenRouterAPIError(f"OpenRouter API call failed: {error}")
