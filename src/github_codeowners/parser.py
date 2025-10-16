"""Parser for CODEOWNERS files."""

import re
from pathlib import Path
from typing import Union

from .models import CodeOwner, CodeOwnersEntry, CodeOwnersFile, EntryType


def parse_codeowners(content: str) -> CodeOwnersFile:
    """Parse CODEOWNERS file content.

    Args:
        content: String content of a CODEOWNERS file

    Returns:
        CodeOwnersFile instance
    """
    codeowners_file = CodeOwnersFile()
    lines = content.split("\n")

    for line in lines:
        entry = parse_line(line)
        codeowners_file.add_entry(entry)

    return codeowners_file


def parse_codeowners_file(file_path: Union[str, Path]) -> CodeOwnersFile:
    """Parse a CODEOWNERS file from disk.

    Args:
        file_path: Path to the CODEOWNERS file

    Returns:
        CodeOwnersFile instance
    """
    file_path = Path(file_path)
    content = file_path.read_text(encoding="utf-8")
    return parse_codeowners(content)


def parse_line(line: str) -> CodeOwnersEntry:
    """Parse a single line from a CODEOWNERS file.

    Args:
        line: Single line from the file

    Returns:
        CodeOwnersEntry instance
    """
    # Store the original line
    original_line = line
    stripped = line.strip()

    # Blank line
    if not stripped:
        entry = CodeOwnersEntry.blank()
        entry.raw_line = original_line
        return entry

    # Comment line
    if stripped.startswith("#"):
        comment_text = stripped[1:].strip()
        entry = CodeOwnersEntry.comment(comment_text)
        entry.raw_line = original_line
        return entry

    # Rule line: pattern followed by owners
    # We need to handle inline comments: pattern @owner1 @owner2 #comment

    # First check if there's an inline comment
    inline_comment = None
    line_to_parse = line

    # Look for # that's not part of a pattern or owner
    # We need to be careful: # can appear in patterns, but inline comments
    # are separated by whitespace before the #
    parts = line.split("#", 1)
    if len(parts) == 2:
        # There's a # in the line
        # Check if it's an inline comment (has whitespace before it)
        before_hash = parts[0]
        if before_hash.rstrip() != before_hash:  # Has trailing whitespace
            inline_comment = parts[1].strip()
            line_to_parse = parts[0]

    # Now parse the pattern and owners
    tokens = line_to_parse.split()

    if not tokens:
        # Edge case: line was just whitespace and a comment
        entry = CodeOwnersEntry.blank()
        entry.raw_line = original_line
        return entry

    pattern = tokens[0]
    owner_tokens = tokens[1:]

    # Parse owners
    owners = []
    for owner_token in owner_tokens:
        try:
            owner = CodeOwner.from_string(owner_token)
            owners.append(owner)
        except ValueError:
            # Invalid owner format, skip it
            # In a real-world scenario, you might want to log this
            pass

    entry = CodeOwnersEntry.rule(pattern, owners, inline_comment)
    entry.raw_line = original_line
    return entry


def find_codeowners_file(repo_path: Union[str, Path]) -> Path:
    """Find the CODEOWNERS file in a repository.

    Searches in the following order:
    1. .github/CODEOWNERS
    2. CODEOWNERS (root)
    3. docs/CODEOWNERS

    Args:
        repo_path: Path to the repository root

    Returns:
        Path to the CODEOWNERS file

    Raises:
        FileNotFoundError: If no CODEOWNERS file is found
    """
    repo_path = Path(repo_path)

    search_paths = [
        repo_path / ".github" / "CODEOWNERS",
        repo_path / "CODEOWNERS",
        repo_path / "docs" / "CODEOWNERS",
    ]

    for path in search_paths:
        if path.exists():
            return path

    raise FileNotFoundError(
        f"No CODEOWNERS file found in {repo_path}. "
        f"Searched: .github/CODEOWNERS, CODEOWNERS, docs/CODEOWNERS"
    )