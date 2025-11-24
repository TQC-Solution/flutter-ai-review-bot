"""Prompt builder for constructing AI review prompts.

Handles loading of:
- Prompt templates (language-specific)
- Coding guidelines
- Building final prompts with proper formatting
"""

import os
import textwrap

from .config import Config
from .diff_chunker import DiffChunker, DiffChunk


class PromptBuilder:
    """Builder class for constructing code review prompts."""

    def __init__(self, language: str = "vietnamese"):
        """Initialize prompt builder.

        Args:
            language: Language for prompts ('vietnamese' or 'english')
        """
        self.language = language
        self.script_dir = os.path.dirname(os.path.dirname(__file__))
        self.chunker = DiffChunker()

    def build_prompt(self, diff_text: str) -> str:
        """Build complete review prompt from diff and templates.

        Args:
            diff_text: The PR diff to review

        Returns:
            Complete prompt string ready for AI
        """
        # Smart truncation: cut at file boundaries to avoid incomplete diffs
        short_diff, was_truncated = self._truncate_diff_smartly(
            diff_text, Config.MAX_DIFF_LENGTH
        )

        # Load coding rules
        coding_rules = self._load_coding_rules()

        # Load prompt template
        prompt_template = self._load_prompt_template()

        # Add truncation warning if needed
        truncation_warning = ""
        if was_truncated and Config.WARN_DIFF_TRUNCATED:
            truncation_warning = self._get_truncation_warning()

        # Build final prompt
        prompt = prompt_template.format(
            coding_rules=coding_rules,
            code_diff=short_diff + truncation_warning
        )

        return prompt

    def build_chunked_prompts(self, diff_text: str) -> list[tuple[str, DiffChunk]]:
        """Build multiple prompts for large diffs using chunking strategy.

        Args:
            diff_text: The PR diff to review

        Returns:
            List of (prompt, chunk) tuples for each chunk to review
        """
        # Check if chunking is needed
        if not self.chunker.should_chunk(diff_text):
            # Single-pass review
            prompt = self.build_prompt(diff_text)
            chunk = DiffChunk(diff_text, ["all"], 0, 1)
            return [(prompt, chunk)]

        # Chunk the diff
        chunks = self.chunker.chunk_diff(diff_text)
        print(f"   📦 Large PR detected: splitting into {len(chunks)} chunks")

        # Load common parts once
        coding_rules = self._load_coding_rules()
        prompt_template = self._load_prompt_template()

        # Build prompts for each chunk
        prompts = []
        for chunk in chunks:
            # Add chunk header
            chunk_header = chunk.get_header(self.language)
            chunk_info = ""

            if chunk.total_chunks > 1:
                if self.language == "english":
                    chunk_info = f"\n\n**NOTE**: This is part {chunk.chunk_index + 1} of {chunk.total_chunks}. Focus on reviewing these specific files only.\n"
                else:
                    chunk_info = f"\n\n**LƯU Ý**: Đây là phần {chunk.chunk_index + 1}/{chunk.total_chunks}. Hãy tập trung review các files này.\n"

            # Build prompt for this chunk
            prompt = prompt_template.format(
                coding_rules=coding_rules,
                code_diff=chunk_header + chunk_info + chunk.content
            )

            prompts.append((prompt, chunk))

        return prompts

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

    def _truncate_diff_smartly(self, diff_text: str, max_length: int) -> tuple[str, bool]:
        """Truncate diff at file boundaries to preserve structure integrity.

        Args:
            diff_text: Full diff text
            max_length: Maximum allowed length

        Returns:
            Tuple of (truncated_diff, was_truncated)
        """
        if len(diff_text) <= max_length:
            return diff_text, False

        # Find all file boundaries (diff --git markers)
        file_markers = []
        lines = diff_text.split('\n')
        current_pos = 0

        for i, line in enumerate(lines):
            if line.startswith('diff --git '):
                file_markers.append({
                    'line_num': i,
                    'position': current_pos,
                    'file_path': self._extract_file_path(line)
                })
            current_pos += len(line) + 1  # +1 for newline

        if not file_markers:
            # No file markers found, use simple truncation
            print("   ⚠️ No diff markers found, using simple truncation")
            return diff_text[:max_length], True

        # Find last complete file that fits within limit
        # A file is "complete" if the NEXT file marker or end-of-diff is within limit
        last_complete_file_idx = -1

        for i, marker in enumerate(file_markers):
            # Check if next file marker or end of diff is within limit
            if i + 1 < len(file_markers):
                next_marker_pos = file_markers[i + 1]['position']
                if next_marker_pos <= max_length:
                    last_complete_file_idx = i
            else:
                # This is the last file - check if it starts within limit
                if marker['position'] < max_length:
                    last_complete_file_idx = i

        if last_complete_file_idx == -1:
            # Even first file doesn't fit, truncate at max_length
            print("   ⚠️ First file too large, truncating at max length")
            return diff_text[:max_length], True

        # Calculate position to cut (at next file or end)
        if last_complete_file_idx + 1 < len(file_markers):
            cut_position = file_markers[last_complete_file_idx + 1]['position']
            is_truncated = True  # There are more files after this
        else:
            # Last file - include everything
            cut_position = len(diff_text)
            is_truncated = False

        truncated = diff_text[:cut_position].rstrip()
        total_files = len(file_markers)
        included_files = last_complete_file_idx + 1

        if is_truncated:
            print(f"   ⚠️ Diff truncated: {included_files}/{total_files} files included "
                  f"({len(truncated)}/{len(diff_text)} chars)")

        return truncated, is_truncated

    def _extract_file_path(self, diff_line: str) -> str:
        """Extract file path from 'diff --git a/path b/path' line.

        Args:
            diff_line: Line starting with 'diff --git'

        Returns:
            File path (b/ path)
        """
        parts = diff_line.split(' ')
        if len(parts) >= 4:
            return parts[3]  # b/path/to/file
        return "unknown"

    def _get_truncation_warning(self) -> str:
        """Get truncation warning message based on language.

        Returns:
            Warning message to append to diff
        """
        if self.language == "english":
            return textwrap.dedent("""

            ⚠️ **IMPORTANT**: The diff above was truncated due to size limits.
            Only the first portion of changed files is shown.
            Please review ONLY the code that is visible above.
            """)
        else:  # Vietnamese
            return textwrap.dedent("""

            ⚠️ **LƯU Ý QUAN TRỌNG**: Diff phía trên đã bị cắt bớt do giới hạn kích thước.
            Chỉ hiển thị phần đầu của các file thay đổi.
            Hãy chỉ review code mà bạn NHÌN THẤY ở phía trên.
            KHÔNG đưa ra nhận xét về các file không có trong diff.
            """)
