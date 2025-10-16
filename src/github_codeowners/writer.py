"""Writer for CODEOWNERS files."""

from pathlib import Path
from typing import Union

from .models import CodeOwnersFile, CodeOwnersEntry, EntryType, CodeOwnersFileSizeError

# GitHub's CODEOWNERS file size limit (3 MB)
MAX_FILE_SIZE_BYTES = 3 * 1024 * 1024  # 3,145,728 bytes


def _validate_file_size(content: str) -> None:
    """Validate that the content doesn't exceed GitHub's 3MB limit.

    Args:
        content: The CODEOWNERS file content

    Raises:
        CodeOwnersFileSizeError: If content exceeds 3MB
    """
    size_bytes = len(content.encode('utf-8'))
    if size_bytes > MAX_FILE_SIZE_BYTES:
        size_mb = size_bytes / (1024 * 1024)
        raise CodeOwnersFileSizeError(
            f"CODEOWNERS file size ({size_mb:.2f} MB) exceeds GitHub's 3 MB limit. "
            f"The file must be under 3 MB to be processed by GitHub."
        )


def write_codeowners(codeowners_file: CodeOwnersFile, validate_size: bool = True) -> str:
    """Convert a CodeOwnersFile to string content.

    Args:
        codeowners_file: CodeOwnersFile instance to serialize
        validate_size: Whether to validate the file size (default: True)

    Returns:
        String content suitable for writing to a CODEOWNERS file

    Raises:
        CodeOwnersFileSizeError: If the content exceeds 3MB and validate_size is True
    """
    lines = []

    for entry in codeowners_file.entries:
        line = format_entry(entry)
        lines.append(line)

    content = "\n".join(lines)

    if validate_size:
        _validate_file_size(content)

    return content


def write_codeowners_file(
    codeowners_file: CodeOwnersFile,
    file_path: Union[str, Path],
    create_dirs: bool = True,
    validate_size: bool = True
) -> None:
    """Write a CodeOwnersFile to disk.

    Args:
        codeowners_file: CodeOwnersFile instance to write
        file_path: Path where the file should be written
        create_dirs: Whether to create parent directories if they don't exist
        validate_size: Whether to validate the file size (default: True)

    Raises:
        CodeOwnersFileSizeError: If the content exceeds 3MB and validate_size is True
    """
    file_path = Path(file_path)

    if create_dirs:
        file_path.parent.mkdir(parents=True, exist_ok=True)

    content = write_codeowners(codeowners_file, validate_size=validate_size)
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