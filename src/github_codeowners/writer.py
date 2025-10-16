"""Writer for CODEOWNERS files."""

from pathlib import Path
from typing import Union

from .models import CodeOwnersFile, CodeOwnersEntry, EntryType


def write_codeowners(codeowners_file: CodeOwnersFile) -> str:
    """Convert a CodeOwnersFile to string content.

    Args:
        codeowners_file: CodeOwnersFile instance to serialize

    Returns:
        String content suitable for writing to a CODEOWNERS file
    """
    lines = []

    for entry in codeowners_file.entries:
        line = format_entry(entry)
        lines.append(line)

    return "\n".join(lines)


def write_codeowners_file(
    codeowners_file: CodeOwnersFile,
    file_path: Union[str, Path],
    create_dirs: bool = True
) -> None:
    """Write a CodeOwnersFile to disk.

    Args:
        codeowners_file: CodeOwnersFile instance to write
        file_path: Path where the file should be written
        create_dirs: Whether to create parent directories if they don't exist
    """
    file_path = Path(file_path)

    if create_dirs:
        file_path.parent.mkdir(parents=True, exist_ok=True)

    content = write_codeowners(codeowners_file)
    file_path.write_text(content, encoding="utf-8")


def format_entry(entry: CodeOwnersEntry) -> str:
    """Format a single CodeOwnersEntry as a string.

    Args:
        entry: Entry to format

    Returns:
        Formatted string representation
    """
    if entry.type == EntryType.BLANK:
        return ""

    if entry.type == EntryType.COMMENT:
        # Format comment with # prefix
        comment_text = entry.comment or ""
        if comment_text:
            return f"# {comment_text}"
        else:
            return "#"

    if entry.type == EntryType.RULE:
        # Format rule: pattern owner1 owner2 [# comment]
        if not entry.pattern:
            return ""

        parts = [entry.pattern]

        # Add owners
        for owner in entry.owners:
            parts.append(str(owner))

        # Add inline comment if present
        if entry.comment:
            parts.append(f"# {entry.comment}")

        return " ".join(parts)

    return ""