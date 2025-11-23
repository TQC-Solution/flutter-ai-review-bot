"""Prompt builder for constructing AI review prompts.

Handles loading of:
- Prompt templates (language-specific)
- Coding guidelines
- Building final prompts with proper formatting
"""

import os
import textwrap

from .config import Config


class PromptBuilder:
    """Builder class for constructing code review prompts."""

    def __init__(self, language: str = "vietnamese"):
        """Initialize prompt builder.

        Args:
            language: Language for prompts ('vietnamese' or 'english')
        """
        self.language = language
        self.script_dir = os.path.dirname(os.path.dirname(__file__))

    def build_prompt(self, diff_text: str) -> str:
        """Build complete review prompt from diff and templates.

        Args:
            diff_text: The PR diff to review

        Returns:
            Complete prompt string ready for AI
        """
        # Limit diff size to avoid huge token payloads
        short_diff = diff_text[:Config.MAX_DIFF_LENGTH]

        # Load coding rules
        coding_rules = self._load_coding_rules()

        # Load prompt template
        prompt_template = self._load_prompt_template()

        # Build final prompt
        prompt = prompt_template.format(
            coding_rules=coding_rules,
            code_diff=short_diff
        )

        return prompt

    def _load_coding_rules(self) -> str:
        """Load coding rules from all rule files in the rule/ directory.

        Returns:
            Combined coding rules text from all rule files or fallback minimal rules
        """
        rules_dir = os.path.join(self.script_dir, "rule")

        try:
            # Get all markdown files in the rule directory
            rule_files = sorted([
                f for f in os.listdir(rules_dir)
                if f.endswith('.md')
            ])

            if not rule_files:
                print(f"⚠️ Warning: No rule files found in {rules_dir}")
                return self._get_fallback_rules()

            # Load and combine all rule files
            all_rules = []
            for rule_file in rule_files:
                rule_path = os.path.join(rules_dir, rule_file)
                try:
                    with open(rule_path, "r", encoding="utf-8") as f:
                        rule_content = f.read()
                        all_rules.append(rule_content)
                    print(f"   ✅ Loaded rule: {rule_file}")
                except Exception as e:
                    print(f"⚠️ Warning: Could not load rule file {rule_file}: {e}")

            if not all_rules:
                print(f"⚠️ Warning: No rules could be loaded")
                return self._get_fallback_rules()

            # Combine all rules with separators
            combined_rules = "\n\n---\n\n".join(all_rules)
            print(f"   ✅ Successfully loaded {len(all_rules)} rule file(s)")
            return combined_rules

        except Exception as e:
            print(f"⚠️ Warning: Could not access rules directory {rules_dir}: {e}")
            return self._get_fallback_rules()

    def _load_prompt_template(self) -> str:
        """Load prompt template based on language.

        Returns:
            Prompt template string with {coding_rules} and {code_diff} placeholders
        """
        if self.language == "english":
            prompt_file = os.path.join(
                self.script_dir, "prompts", "review_prompt_en.txt"
            )
        else:  # Vietnamese (default)
            prompt_file = os.path.join(
                self.script_dir, "prompts", "review_prompt_vi.txt"
            )

        try:
            with open(prompt_file, "r", encoding="utf-8") as f:
                template = f.read()
            print(f"   ✅ Loaded prompt template: {prompt_file}")
            return template
        except Exception as e:
            print(f"⚠️ Warning: Could not load prompt file from {prompt_file}: {e}")
            return self._get_fallback_template()

    def _get_fallback_rules(self) -> str:
        """Get fallback coding rules if file cannot be loaded.

        Returns:
            Minimal coding rules
        """
        return textwrap.dedent("""
        ## Key Flutter Review Rules:
        - Clean Architecture: Domain must NOT import Data/Presentation layers
        - GetX: Use init: only at root widget, Get.find() in children
        - Assets: Use Assets.icons.iconBack (NOT hardcoded paths)
        - i18n: Use context.tr() (NOT hardcoded strings)
        - Error Handling: Return Either<Failure, T> in repositories
        """)

    def _get_fallback_template(self) -> str:
        """Get fallback prompt template if file cannot be loaded.

        Returns:
            Fallback Vietnamese template
        """
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
