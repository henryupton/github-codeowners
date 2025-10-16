"""Tests for github_codeowners.writer module."""

import pytest
from pathlib import Path

from github_codeowners.writer import (
    write_codeowners,
    write_codeowners_file,
    format_entry,
    MAX_FILE_SIZE_BYTES,
)
from github_codeowners.models import (
    CodeOwnersFile,
    CodeOwnersEntry,
    EntryType,
    CodeOwnersFileSizeError,
)
from github_codeowners.parser import parse_codeowners


class TestFormatEntry:
    """Tests for format_entry function."""

    def test_format_blank_entry(self):
        """Test formatting a blank entry."""
        entry = CodeOwnersEntry.blank()
        result = format_entry(entry)
        assert result == ""

    def test_format_comment_entry(self):
        """Test formatting a comment entry."""
        entry = CodeOwnersEntry.comment("This is a comment")
        result = format_entry(entry)
        assert result == "# This is a comment"

    def test_format_comment_empty(self):
        """Test formatting an empty comment."""
        entry = CodeOwnersEntry.comment("")
        result = format_entry(entry)
        assert result == "#"

    def test_format_simple_rule(self):
        """Test formatting a simple rule."""
        entry = CodeOwnersEntry.rule("*.py", ["@python-team"])
        result = format_entry(entry)
        assert result == "*.py @python-team"

    def test_format_rule_multiple_owners(self):
        """Test formatting a rule with multiple owners."""
        entry = CodeOwnersEntry.rule("*.py", ["@python-team", "@senior-dev", "@code-reviewer"])
        result = format_entry(entry)
        assert result == "*.py @python-team @senior-dev @code-reviewer"

    def test_format_rule_with_inline_comment(self):
        """Test formatting a rule with inline comment."""
        entry = CodeOwnersEntry.rule("*.html", ["@frontend-team"], inline_comment="Web pages")
        result = format_entry(entry)
        assert result == "*.html @frontend-team # Web pages"

    def test_format_rule_with_team_owner(self):
        """Test formatting a rule with team owner."""
        entry = CodeOwnersEntry.rule("*.py", ["@myorg/python-team"])
        result = format_entry(entry)
        assert result == "*.py @myorg/python-team"

    def test_format_rule_with_email_owner(self):
        """Test formatting a rule with email owner."""
        entry = CodeOwnersEntry.rule("docs/**", ["@docs-team", "user@example.com"])
        result = format_entry(entry)
        assert result == "docs/** @docs-team user@example.com"

    def test_format_rule_no_pattern(self):
        """Test formatting a rule with no pattern returns empty string."""
        entry = CodeOwnersEntry(type=EntryType.RULE, pattern=None, owners=[])
        result = format_entry(entry)
        assert result == ""


class TestWriteCodeowners:
    """Tests for write_codeowners function."""

    def test_write_empty_file(self):
        """Test writing an empty file."""
        codeowners = CodeOwnersFile()
        result = write_codeowners(codeowners)
        assert result == ""

    def test_write_single_rule(self):
        """Test writing a file with single rule."""
        codeowners = CodeOwnersFile()
        codeowners.add_rule("*.py", ["@python-team"])
        result = write_codeowners(codeowners)
        assert result == "*.py @python-team"

    def test_write_multiple_rules(self):
        """Test writing a file with multiple rules."""
        codeowners = CodeOwnersFile()
        codeowners.add_rule("*.py", ["@python-team"])
        codeowners.add_rule("*.js", ["@js-team"])
        result = write_codeowners(codeowners)

        lines = result.split("\n")
        assert len(lines) == 2
        assert lines[0] == "*.py @python-team"
        assert lines[1] == "*.js @js-team"

    def test_write_with_comments(self):
        """Test writing a file with comments."""
        codeowners = CodeOwnersFile()
        codeowners.add_comment("Python files")
        codeowners.add_rule("*.py", ["@python-team"])
        result = write_codeowners(codeowners)

        lines = result.split("\n")
        assert len(lines) == 2
        assert lines[0] == "# Python files"
        assert lines[1] == "*.py @python-team"

    def test_write_with_blank_lines(self):
        """Test writing a file with blank lines."""
        codeowners = CodeOwnersFile()
        codeowners.add_rule("*.py", ["@python-team"])
        codeowners.add_blank()
        codeowners.add_rule("*.js", ["@js-team"])
        result = write_codeowners(codeowners)

        lines = result.split("\n")
        assert len(lines) == 3
        assert lines[0] == "*.py @python-team"
        assert lines[1] == ""
        assert lines[2] == "*.js @js-team"

    def test_write_complex_structure(self):
        """Test writing a complex file structure."""
        codeowners = CodeOwnersFile()

        codeowners.add_comment("Default owner")
        codeowners.add_rule("*", ["@default-owner"])
        codeowners.add_blank()

        codeowners.add_comment("Python files")
        codeowners.add_rule("*.py", ["@python-team", "@senior-dev"])
        codeowners.add_blank()

        codeowners.add_comment("Frontend")
        codeowners.add_rule("*.js", ["@frontend-team"])
        codeowners.add_rule("*.html", ["@frontend-team"], inline_comment="Web pages")

        result = write_codeowners(codeowners)
        lines = result.split("\n")

        assert "# Default owner" in lines
        assert "* @default-owner" in lines
        assert "# Python files" in lines
        assert "*.py @python-team @senior-dev" in lines
        assert "*.html @frontend-team # Web pages" in lines

    def test_write_from_sample_fixture(self, sample_codeowners_file):
        """Test writing the sample fixture."""
        result = write_codeowners(sample_codeowners_file)
        assert len(result) > 0

        # Should be able to parse it back
        reparsed = parse_codeowners(result)
        assert len(reparsed.get_rules()) == len(sample_codeowners_file.get_rules())


class TestWriteCodeownersFile:
    """Tests for write_codeowners_file function."""

    def test_write_to_file(self, tmp_path):
        """Test writing to a file."""
        codeowners = CodeOwnersFile()
        codeowners.add_rule("*.py", ["@python-team"])
        codeowners.add_rule("*.js", ["@js-team"])

        output_file = tmp_path / "CODEOWNERS"
        write_codeowners_file(codeowners, output_file)

        assert output_file.exists()
        content = output_file.read_text()
        assert "*.py @python-team" in content
        assert "*.js @js-team" in content

    def test_write_with_string_path(self, tmp_path):
        """Test writing with string path."""
        codeowners = CodeOwnersFile()
        codeowners.add_rule("*.py", ["@python-team"])

        output_file = tmp_path / "CODEOWNERS"
        write_codeowners_file(codeowners, str(output_file))

        assert output_file.exists()

    def test_write_with_path_object(self, tmp_path):
        """Test writing with Path object."""
        codeowners = CodeOwnersFile()
        codeowners.add_rule("*.py", ["@python-team"])

        output_file = tmp_path / "CODEOWNERS"
        write_codeowners_file(codeowners, Path(output_file))

        assert output_file.exists()

    def test_write_creates_parent_directories(self, tmp_path):
        """Test that parent directories are created."""
        codeowners = CodeOwnersFile()
        codeowners.add_rule("*.py", ["@python-team"])

        output_file = tmp_path / "nested" / "dir" / "CODEOWNERS"
        write_codeowners_file(codeowners, output_file, create_dirs=True)

        assert output_file.exists()
        assert output_file.parent.exists()

    def test_write_no_create_dirs_fails(self, tmp_path):
        """Test that writing fails without create_dirs when parent doesn't exist."""
        codeowners = CodeOwnersFile()
        codeowners.add_rule("*.py", ["@python-team"])

        output_file = tmp_path / "nested" / "dir" / "CODEOWNERS"
        with pytest.raises(FileNotFoundError):
            write_codeowners_file(codeowners, output_file, create_dirs=False)

    def test_write_overwrites_existing_file(self, tmp_path):
        """Test that writing overwrites existing file."""
        output_file = tmp_path / "CODEOWNERS"
        output_file.write_text("old content")

        codeowners = CodeOwnersFile()
        codeowners.add_rule("*.py", ["@python-team"])
        write_codeowners_file(codeowners, output_file)

        content = output_file.read_text()
        assert "old content" not in content
        assert "*.py @python-team" in content


class TestRoundTrip:
    """Tests for parsing and writing round trips."""

    def test_simple_round_trip(self, simple_codeowners_content):
        """Test that parsing and writing produces equivalent content."""
        # Parse
        codeowners = parse_codeowners(simple_codeowners_content)

        # Write
        written = write_codeowners(codeowners)

        # Parse again
        reparsed = parse_codeowners(written)

        # Should have same number of rules
        assert len(codeowners.get_rules()) == len(reparsed.get_rules())

        # Rules should match
        for original, reparsed_rule in zip(codeowners.get_rules(), reparsed.get_rules()):
            assert original.pattern == reparsed_rule.pattern
            assert len(original.owners) == len(reparsed_rule.owners)

    def test_complex_round_trip(self, complex_codeowners_content):
        """Test round trip with complex content."""
        # Parse
        codeowners = parse_codeowners(complex_codeowners_content)

        # Write
        written = write_codeowners(codeowners)

        # Parse again
        reparsed = parse_codeowners(written)

        # Should have same number of rules
        assert len(codeowners.get_rules()) == len(reparsed.get_rules())

        # Check specific patterns
        original_patterns = {rule.pattern for rule in codeowners.get_rules()}
        reparsed_patterns = {rule.pattern for rule in reparsed.get_rules()}
        assert original_patterns == reparsed_patterns

    def test_round_trip_preserves_inline_comments(self):
        """Test that inline comments are preserved in round trip."""
        content = """*.html @frontend # HTML files
*.css @frontend # CSS files
"""
        codeowners = parse_codeowners(content)
        written = write_codeowners(codeowners)
        reparsed = parse_codeowners(written)

        rules = reparsed.get_rules()
        assert rules[0].comment == "HTML files"
        assert rules[1].comment == "CSS files"

    def test_round_trip_with_file(self, tmp_path, sample_codeowners_content):
        """Test round trip through file system."""
        # Write original content
        input_file = tmp_path / "CODEOWNERS.in"
        input_file.write_text(sample_codeowners_content)

        # Parse from file
        from github_codeowners.parser import parse_codeowners_file
        codeowners = parse_codeowners_file(input_file)

        # Write to new file
        output_file = tmp_path / "CODEOWNERS.out"
        write_codeowners_file(codeowners, output_file)

        # Parse new file
        reparsed = parse_codeowners_file(output_file)

        # Should have same rules
        assert len(codeowners.get_rules()) == len(reparsed.get_rules())


class TestFileSizeValidation:
    """Tests for CODEOWNERS file size validation."""

    def test_write_within_size_limit(self):
        """Test that files within the size limit write successfully."""
        codeowners = CodeOwnersFile()
        codeowners.add_rule("*.py", ["@python-team"])
        
        # Should not raise an exception
        content = write_codeowners(codeowners)
        assert len(content.encode('utf-8')) < MAX_FILE_SIZE_BYTES

    def test_write_exceeds_size_limit(self):
        """Test that files exceeding 3MB raise an error."""
        codeowners = CodeOwnersFile()

        # Create a very large CODEOWNERS file (over 3MB)
        # Add many rules with long patterns and comments
        large_pattern = "a" * 1500
        large_comment = "b" * 1500

        # Add enough rules to exceed 3MB
        # Each rule is approximately 3000+ bytes, so we need ~1100 rules
        for i in range(1200):
            codeowners.add_rule(
                f"{large_pattern}_{i}",
                ["@team1", "@team2", "@team3"],
                inline_comment=f"{large_comment}_{i}"
            )

        # Should raise CodeOwnersFileSizeError
        with pytest.raises(CodeOwnersFileSizeError) as exc_info:
            write_codeowners(codeowners)

        assert "3 MB limit" in str(exc_info.value)

    def test_write_file_exceeds_size_limit(self, tmp_path):
        """Test that write_codeowners_file also validates size."""
        codeowners = CodeOwnersFile()

        # Create a large file
        large_pattern = "x" * 1500
        for i in range(1200):
            codeowners.add_rule(
                f"{large_pattern}_{i}",
                ["@team1", "@team2"],
                inline_comment="c" * 1500
            )

        output_file = tmp_path / "CODEOWNERS"

        # Should raise CodeOwnersFileSizeError
        with pytest.raises(CodeOwnersFileSizeError):
            write_codeowners_file(codeowners, output_file)

        # File should not be created
        assert not output_file.exists()

    def test_write_with_validation_disabled(self):
        """Test that validation can be disabled."""
        codeowners = CodeOwnersFile()

        # Create a large file
        large_pattern = "y" * 1500
        for i in range(1200):
            codeowners.add_rule(
                f"{large_pattern}_{i}",
                ["@team1", "@team2"],
                inline_comment="d" * 1500
            )

        # Should not raise an exception when validate_size=False
        content = write_codeowners(codeowners, validate_size=False)
        assert len(content.encode('utf-8')) > MAX_FILE_SIZE_BYTES

    def test_write_file_with_validation_disabled(self, tmp_path):
        """Test that file validation can be disabled."""
        codeowners = CodeOwnersFile()

        # Create a large file
        large_pattern = "z" * 1500
        for i in range(1200):
            codeowners.add_rule(
                f"{large_pattern}_{i}",
                ["@team1", "@team2"],
                inline_comment="e" * 1500
            )

        output_file = tmp_path / "CODEOWNERS"

        # Should not raise when validation is disabled
        write_codeowners_file(codeowners, output_file, validate_size=False)
        assert output_file.exists()

        # Verify the file is large
        size_bytes = output_file.stat().st_size
        assert size_bytes > MAX_FILE_SIZE_BYTES

    def test_size_error_message_includes_actual_size(self):
        """Test that the error message includes the actual file size."""
        codeowners = CodeOwnersFile()

        # Create a file that exceeds 3MB
        large_pattern = "p" * 1500
        for i in range(1200):
            codeowners.add_rule(
                f"{large_pattern}_{i}",
                ["@team1", "@team2"],
                inline_comment="f" * 1500
            )

        with pytest.raises(CodeOwnersFileSizeError) as exc_info:
            write_codeowners(codeowners)

        error_message = str(exc_info.value)
        # Error should mention the size in MB
        assert "MB" in error_message
        # Error should mention the 3 MB limit
        assert "3 MB" in error_message
