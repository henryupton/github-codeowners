"""Tests for github_codeowners.parser module."""

import pytest
from pathlib import Path

from github_codeowners.parser import (
    parse_codeowners,
    parse_codeowners_file,
    parse_line,
    find_codeowners_file,
)
from github_codeowners.models import EntryType, OwnerType


class TestParseLine:
    """Tests for parse_line function."""

    def test_parse_blank_line(self):
        """Test parsing a blank line."""
        entry = parse_line("")
        assert entry.is_blank()

        entry = parse_line("   ")
        assert entry.is_blank()

        entry = parse_line("\t\t")
        assert entry.is_blank()

    def test_parse_comment_line(self):
        """Test parsing a comment line."""
        entry = parse_line("# This is a comment")
        assert entry.is_comment()
        assert entry.comment == "This is a comment"

        entry = parse_line("#Another comment")
        assert entry.is_comment()
        assert entry.comment == "Another comment"

        entry = parse_line("  # Indented comment")
        assert entry.is_comment()
        assert entry.comment == "Indented comment"

    def test_parse_simple_rule(self):
        """Test parsing a simple rule."""
        entry = parse_line("*.py @python-team")
        assert entry.is_rule()
        assert entry.pattern == "*.py"
        assert len(entry.owners) == 1
        assert entry.owners[0].value == "@python-team"
        assert entry.comment is None

    def test_parse_rule_multiple_owners(self):
        """Test parsing a rule with multiple owners."""
        entry = parse_line("*.py @python-team @senior-dev @code-reviewer")
        assert entry.is_rule()
        assert entry.pattern == "*.py"
        assert len(entry.owners) == 3
        assert entry.owners[0].value == "@python-team"
        assert entry.owners[1].value == "@senior-dev"
        assert entry.owners[2].value == "@code-reviewer"

    def test_parse_rule_with_inline_comment(self):
        """Test parsing a rule with inline comment."""
        entry = parse_line("*.html @frontend-team # Web pages")
        assert entry.is_rule()
        assert entry.pattern == "*.html"
        assert len(entry.owners) == 1
        assert entry.owners[0].value == "@frontend-team"
        assert entry.comment == "Web pages"

    def test_parse_rule_with_team_owner(self):
        """Test parsing a rule with team owner."""
        entry = parse_line("*.py @myorg/python-team")
        assert entry.is_rule()
        assert len(entry.owners) == 1
        assert entry.owners[0].value == "@myorg/python-team"
        assert entry.owners[0].type == OwnerType.TEAM

    def test_parse_rule_with_email_owner(self):
        """Test parsing a rule with email owner."""
        entry = parse_line("docs/** @docs-team user@example.com")
        assert entry.is_rule()
        assert len(entry.owners) == 2
        assert entry.owners[0].value == "@docs-team"
        assert entry.owners[0].type == OwnerType.USERNAME
        assert entry.owners[1].value == "user@example.com"
        assert entry.owners[1].type == OwnerType.EMAIL

    def test_parse_rule_with_path_pattern(self):
        """Test parsing rules with various path patterns."""
        entry = parse_line("/docs/** @docs-team")
        assert entry.pattern == "/docs/**"

        entry = parse_line("src/frontend/** @frontend-team")
        assert entry.pattern == "src/frontend/**"

        entry = parse_line("* @default-owner")
        assert entry.pattern == "*"

    def test_parse_rule_preserves_raw_line(self):
        """Test that raw line is preserved."""
        line = "*.py @python-team # Python files"
        entry = parse_line(line)
        assert entry.raw_line == line

    def test_parse_mixed_owner_types(self):
        """Test parsing rule with mixed owner types."""
        entry = parse_line("/shared/** @backend-team @frontend-team @myorg/platform email@example.com")
        assert entry.is_rule()
        assert len(entry.owners) == 4
        assert entry.owners[0].type == OwnerType.USERNAME
        assert entry.owners[1].type == OwnerType.USERNAME
        assert entry.owners[2].type == OwnerType.TEAM
        assert entry.owners[3].type == OwnerType.EMAIL


class TestParseCodeowners:
    """Tests for parse_codeowners function."""

    def test_parse_empty_string(self):
        """Test parsing an empty string."""
        codeowners = parse_codeowners("")
        assert len(codeowners.entries) == 1  # Just the empty line
        assert codeowners.entries[0].is_blank()

    def test_parse_simple_content(self, simple_codeowners_content):
        """Test parsing simple content."""
        codeowners = parse_codeowners(simple_codeowners_content)
        assert len(codeowners.entries) > 0

        rules = codeowners.get_rules()
        assert len(rules) == 2

    def test_parse_sample_content(self, sample_codeowners_content):
        """Test parsing sample content."""
        codeowners = parse_codeowners(sample_codeowners_content)

        # Check we have entries
        assert len(codeowners.entries) > 0

        # Check we have rules
        rules = codeowners.get_rules()
        assert len(rules) > 0

        # Check for specific patterns
        py_rules = codeowners.find_rules_for_pattern("*.py")
        assert len(py_rules) == 1
        assert len(py_rules[0].owners) == 2

    def test_parse_complex_content(self, complex_codeowners_content):
        """Test parsing complex content with various features."""
        codeowners = parse_codeowners(complex_codeowners_content)

        # Should have multiple entries
        assert len(codeowners.entries) > 10

        # Check rules
        rules = codeowners.get_rules()
        assert len(rules) > 5

        # Check for comments
        comments = [e for e in codeowners.entries if e.is_comment()]
        assert len(comments) > 0

        # Check for blank lines
        blanks = [e for e in codeowners.entries if e.is_blank()]
        assert len(blanks) > 0

        # Check specific patterns
        backend_rules = codeowners.find_rules_for_pattern("/backend/**")
        assert len(backend_rules) == 1
        assert len(backend_rules[0].owners) >= 2

    def test_parse_preserves_structure(self):
        """Test that parsing preserves file structure."""
        content = """# Comment 1

*.py @python-team

# Comment 2
*.js @js-team
"""
        codeowners = parse_codeowners(content)

        # Should have: comment, blank, rule, blank, comment, rule, blank
        assert len(codeowners.entries) == 7
        assert codeowners.entries[0].is_comment()
        assert codeowners.entries[1].is_blank()
        assert codeowners.entries[2].is_rule()
        assert codeowners.entries[3].is_blank()
        assert codeowners.entries[4].is_comment()
        assert codeowners.entries[5].is_rule()
        assert codeowners.entries[6].is_blank()

    def test_parse_with_inline_comments(self):
        """Test parsing rules with inline comments."""
        content = """*.html @frontend # HTML files
*.css @frontend # CSS files
*.js @frontend # JavaScript files
"""
        codeowners = parse_codeowners(content)
        rules = codeowners.get_rules()

        assert len(rules) == 3
        assert all(rule.comment is not None for rule in rules)
        assert rules[0].comment == "HTML files"
        assert rules[1].comment == "CSS files"
        assert rules[2].comment == "JavaScript files"


class TestParseCodeownersFile:
    """Tests for parse_codeowners_file function."""

    def test_parse_file(self, temp_codeowners_file):
        """Test parsing a file from disk."""
        codeowners = parse_codeowners_file(temp_codeowners_file)

        assert len(codeowners.entries) > 0
        rules = codeowners.get_rules()
        assert len(rules) > 0

    def test_parse_nonexistent_file(self, tmp_path):
        """Test parsing a nonexistent file raises an error."""
        nonexistent = tmp_path / "nonexistent.txt"
        with pytest.raises(FileNotFoundError):
            parse_codeowners_file(nonexistent)

    def test_parse_file_with_path_string(self, temp_codeowners_file):
        """Test parsing with string path."""
        codeowners = parse_codeowners_file(str(temp_codeowners_file))
        assert len(codeowners.entries) > 0

    def test_parse_file_with_path_object(self, temp_codeowners_file):
        """Test parsing with Path object."""
        codeowners = parse_codeowners_file(Path(temp_codeowners_file))
        assert len(codeowners.entries) > 0


class TestFindCodeownersFile:
    """Tests for find_codeowners_file function."""

    def test_find_in_github_directory(self, tmp_path, sample_codeowners_content):
        """Test finding CODEOWNERS in .github/ directory."""
        github_dir = tmp_path / ".github"
        github_dir.mkdir()
        codeowners_file = github_dir / "CODEOWNERS"
        codeowners_file.write_text(sample_codeowners_content)

        found = find_codeowners_file(tmp_path)
        assert found == codeowners_file

    def test_find_in_root_directory(self, tmp_path, sample_codeowners_content):
        """Test finding CODEOWNERS in root directory."""
        codeowners_file = tmp_path / "CODEOWNERS"
        codeowners_file.write_text(sample_codeowners_content)

        found = find_codeowners_file(tmp_path)
        assert found == codeowners_file

    def test_find_in_docs_directory(self, tmp_path, sample_codeowners_content):
        """Test finding CODEOWNERS in docs/ directory."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        codeowners_file = docs_dir / "CODEOWNERS"
        codeowners_file.write_text(sample_codeowners_content)

        found = find_codeowners_file(tmp_path)
        assert found == codeowners_file

    def test_find_precedence(self, tmp_path, sample_codeowners_content):
        """Test that .github/ takes precedence over root and docs/."""
        # Create in all three locations
        github_dir = tmp_path / ".github"
        github_dir.mkdir()
        github_codeowners = github_dir / "CODEOWNERS"
        github_codeowners.write_text(sample_codeowners_content)

        root_codeowners = tmp_path / "CODEOWNERS"
        root_codeowners.write_text(sample_codeowners_content)

        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        docs_codeowners = docs_dir / "CODEOWNERS"
        docs_codeowners.write_text(sample_codeowners_content)

        # Should find the one in .github/ first
        found = find_codeowners_file(tmp_path)
        assert found == github_codeowners

    def test_find_nonexistent_raises_error(self, tmp_path):
        """Test that nonexistent CODEOWNERS raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            find_codeowners_file(tmp_path)

    def test_find_with_string_path(self, temp_repo_with_codeowners):
        """Test finding with string path."""
        found = find_codeowners_file(str(temp_repo_with_codeowners))
        assert found.exists()

    def test_find_with_path_object(self, temp_repo_with_codeowners):
        """Test finding with Path object."""
        found = find_codeowners_file(Path(temp_repo_with_codeowners))
        assert found.exists()
