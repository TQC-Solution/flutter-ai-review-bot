"""Diff chunker for splitting large diffs into reviewable chunks.

Handles intelligent splitting of PR diffs to avoid:
- Attention degradation in LLMs with long context
- File information being missed in large PRs
- Output truncation issues
"""

from typing import List, Dict, Tuple


class DiffChunk:
    """Represents a chunk of diff to be reviewed."""

    def __init__(self, content: str, files: List[str], chunk_index: int, total_chunks: int):
        """Initialize a diff chunk.

        Args:
            content: The diff content for this chunk
            files: List of file paths included in this chunk
            chunk_index: Index of this chunk (0-based)
            total_chunks: Total number of chunks
        """
        self.content = content
        self.files = files
        self.chunk_index = chunk_index
        self.total_chunks = total_chunks

    def get_header(self, language: str = "vietnamese") -> str:
        """Get chunk header for display.

        Args:
            language: Language for header ('vietnamese' or 'english')

        Returns:
            Formatted header string
        """
        if self.total_chunks == 1:
            return ""

        if language == "english":
            return f"**Chunk {self.chunk_index + 1}/{self.total_chunks}** - Files: {', '.join(self.files)}\n\n"
        else:  # Vietnamese
            return f"**Phần {self.chunk_index + 1}/{self.total_chunks}** - Files: {', '.join(self.files)}\n\n"


class DiffChunker:
    """Intelligent diff chunker that splits by file boundaries."""

    # Thresholds for chunking strategy
    SINGLE_PASS_FILE_THRESHOLD = 5  # If <= 5 files, use single-pass review
    SINGLE_PASS_CHAR_THRESHOLD = 30000  # If <= 30k chars, use single-pass
    MAX_CHUNK_SIZE = 40000  # Max chars per chunk (conservative to avoid attention issues)

    def __init__(self):
        """Initialize diff chunker."""
        pass

    def should_chunk(self, diff_text: str) -> bool:
        """Determine if diff should be chunked.

        Args:
            diff_text: Full PR diff

        Returns:
            True if should use chunking, False for single-pass
        """
        # Parse files from diff
        files = self._extract_file_boundaries(diff_text)

        # Small PRs: single-pass review
        if len(files) <= self.SINGLE_PASS_FILE_THRESHOLD:
            return False

        # Short diffs: single-pass review
        if len(diff_text) <= self.SINGLE_PASS_CHAR_THRESHOLD:
            return False

        # Large PRs: use chunking
        return True

    def chunk_diff(self, diff_text: str) -> List[DiffChunk]:
        """Split diff into chunks by file boundaries.

        Args:
            diff_text: Full PR diff

        Returns:
            List of DiffChunk objects
        """
        files = self._extract_file_boundaries(diff_text)

        # No files found - return as single chunk
        if not files:
            return [DiffChunk(diff_text, ["unknown"], 0, 1)]

        # Single-pass if small enough
        if not self.should_chunk(diff_text):
            file_paths = [f['file_path'] for f in files]
            return [DiffChunk(diff_text, file_paths, 0, 1)]

        # Chunk by files
        chunks = []
        current_chunk_content = ""
        current_chunk_files = []
        chunk_index = 0

        for i, file_info in enumerate(files):
            # Extract this file's diff
            start_pos = file_info['position']
            if i + 1 < len(files):
                end_pos = files[i + 1]['position']
            else:
                end_pos = len(diff_text)

            file_diff = diff_text[start_pos:end_pos]

            # Check if adding this file exceeds chunk size
            if current_chunk_content and len(current_chunk_content) + len(file_diff) > self.MAX_CHUNK_SIZE:
                # Save current chunk
                chunks.append(DiffChunk(
                    current_chunk_content,
                    current_chunk_files,
                    chunk_index,
                    0  # Will update total_chunks later
                ))
                chunk_index += 1
                current_chunk_content = ""
                current_chunk_files = []

            # Add file to current chunk
            current_chunk_content += file_diff
            current_chunk_files.append(file_info['file_path'])

        # Add last chunk
        if current_chunk_content:
            chunks.append(DiffChunk(
                current_chunk_content,
                current_chunk_files,
                chunk_index,
                0
            ))

        # Update total_chunks for all chunks
        total_chunks = len(chunks)
        for chunk in chunks:
            chunk.total_chunks = total_chunks

        return chunks

    def _extract_file_boundaries(self, diff_text: str) -> List[Dict]:
        """Extract file boundaries from diff.

        Args:
            diff_text: The diff text

        Returns:
            List of dicts with file info: {'position': int, 'file_path': str}
        """
        files = []
        lines = diff_text.split('\n')
        current_pos = 0

        for i, line in enumerate(lines):
            if line.startswith('diff --git '):
                # Extract file path (b/path/to/file.dart)
                parts = line.split(' ')
                file_path = parts[3] if len(parts) >= 4 else "unknown"
                # Remove 'b/' prefix
                if file_path.startswith('b/'):
                    file_path = file_path[2:]

                files.append({
                    'position': current_pos,
                    'line_num': i,
                    'file_path': file_path
                })

            current_pos += len(line) + 1  # +1 for newline

        return files
