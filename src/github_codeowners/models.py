"""Data models for CODEOWNERS files."""

from dataclasses import dataclass, field
from typing import List, Optional, Union
from enum import Enum


class CodeOwnersFileSizeError(Exception):
    """Raised when a CODEOWNERS file exceeds GitHub's 3MB size limit."""
    pass


class OwnerType(Enum):
    """Type of code owner."""
    USERNAME = "username"  # @username
    TEAM = "team"  # @org/team-name
    EMAIL = "email"  # user@example.com


@dataclass
class CodeOwner:
    """Represents a single code owner."""

    value: str  # The raw owner string (e.g., "@username", "@org/team", "user@example.com")
    type: OwnerType

    @classmethod
    def from_string(cls, owner_str: str) -> "CodeOwner":
        """Create a CodeOwner from a string.

        Args:
            owner_str: Owner string like "@username", "@org/team", or "email@example.com"

        Returns:
            CodeOwner instance
        """
        owner_str = owner_str.strip()

        if owner_str.startswith("@"):
            if "/" in owner_str:
                return cls(value=owner_str, type=OwnerType.TEAM)
            else:
                return cls(value=owner_str, type=OwnerType.USERNAME)
        elif "@" in owner_str:
            return cls(value=owner_str, type=OwnerType.EMAIL)
        else:
            raise ValueError(f"Invalid owner format: {owner_str}")

    def __str__(self) -> str:
        """Return the string representation of the owner."""
        return self.value


class EntryType(Enum):
    """Type of CODEOWNERS file entry."""
    RULE = "rule"  # Pattern with owners
    COMMENT = "comment"  # Comment line
    BLANK = "blank"  # Empty line


@dataclass
class CodeOwnersEntry:
    """Represents a single line in a CODEOWNERS file."""

    type: EntryType
    pattern: Optional[str] = None  # File pattern (for RULE entries)
    owners: List[CodeOwner] = field(default_factory=list)  # Owners (for RULE entries)
    comment: Optional[str] = None  # Comment text (for COMMENT entries or inline comments)
    raw_line: Optional[str] = None  # Original line for reference

    @classmethod
    def blank(cls) -> "CodeOwnersEntry":
        """Create a blank line entry."""
        return cls(type=EntryType.BLANK, raw_line="")

    @classmethod
    def comment(cls, comment_text: str) -> "CodeOwnersEntry":
        """Create a comment entry.

        Args:
            comment_text: Comment text (without the # prefix)
        """
        return cls(type=EntryType.COMMENT, comment=comment_text, raw_line=f"#{comment_text}")

    @classmethod
    def rule(
        cls,
        pattern: str,
        owners: List[Union[CodeOwner, str]],
        inline_comment: Optional[str] = None
    ) -> "CodeOwnersEntry":
        """Create a rule entry.

        Args:
            pattern: File pattern
            owners: List of CodeOwner instances or owner strings
            inline_comment: Optional inline comment
        """
        # Convert string owners to CodeOwner instances
        owner_objs = [
            owner if isinstance(owner, CodeOwner) else CodeOwner.from_string(owner)
            for owner in owners
        ]

        return cls(
            type=EntryType.RULE,
            pattern=pattern,
            owners=owner_objs,
            comment=inline_comment
        )

    def is_rule(self) -> bool:
        """Check if this entry is a rule."""
        return self.type == EntryType.RULE

    def is_comment(self) -> bool:
        """Check if this entry is a comment."""
        return self.type == EntryType.COMMENT

    def is_blank(self) -> bool:
        """Check if this entry is blank."""
        return self.type == EntryType.BLANK


@dataclass
class CodeOwnersFile:
    """Represents a complete CODEOWNERS file."""

    entries: List[CodeOwnersEntry] = field(default_factory=list)

    def add_entry(self, entry: CodeOwnersEntry) -> None:
        """Add an entry to the file."""
        self.entries.append(entry)

    def add_rule(
        self,
        pattern: str,
        owners: List[Union[CodeOwner, str]],
        inline_comment: Optional[str] = None
    ) -> None:
        """Add a rule entry to the file.

        Args:
            pattern: File pattern
            owners: List of CodeOwner instances or owner strings
            inline_comment: Optional inline comment
        """
        self.add_entry(CodeOwnersEntry.rule(pattern, owners, inline_comment))

    def add_comment(self, comment_text: str) -> None:
        """Add a comment entry to the file.

        Args:
            comment_text: Comment text (without the # prefix)
        """
        self.add_entry(CodeOwnersEntry.comment(comment_text))

    def add_blank(self) -> None:
        """Add a blank line entry to the file."""
        self.add_entry(CodeOwnersEntry.blank())

    def get_rules(self) -> List[CodeOwnersEntry]:
        """Get all rule entries."""
        return [entry for entry in self.entries if entry.is_rule()]

    def find_rules_for_pattern(self, pattern: str) -> List[CodeOwnersEntry]:
        """Find all rules matching a specific pattern.

        Args:
            pattern: Pattern to search for

        Returns:
            List of matching rule entries
        """
        return [entry for entry in self.get_rules() if entry.pattern == pattern]

    def remove_entry(self, entry: CodeOwnersEntry) -> None:
        """Remove an entry from the file.

        Args:
            entry: Entry to remove
        """
        self.entries.remove(entry)

    def clear(self) -> None:
        """Remove all entries from the file."""
        self.entries.clear()