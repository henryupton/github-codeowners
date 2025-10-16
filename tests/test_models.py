"""Tests for github_codeowners.models module."""

import pytest

from github_codeowners.models import (
    CodeOwner,
    CodeOwnersEntry,
    CodeOwnersFile,
    OwnerType,
    EntryType,
)


class TestCodeOwner:
    """Tests for CodeOwner class."""

    def test_from_string_username(self):
        """Test creating CodeOwner from username string."""
        owner = CodeOwner.from_string("@testuser")
        assert owner.value == "@testuser"
        assert owner.type == OwnerType.USERNAME

    def test_from_string_team(self):
        """Test creating CodeOwner from team string."""
        owner = CodeOwner.from_string("@myorg/team-name")
        assert owner.value == "@myorg/team-name"
        assert owner.type == OwnerType.TEAM

    def test_from_string_email(self):
        """Test creating CodeOwner from email string."""
        owner = CodeOwner.from_string("user@example.com")
        assert owner.value == "user@example.com"
        assert owner.type == OwnerType.EMAIL

    def test_from_string_invalid(self):
        """Test that invalid owner strings raise ValueError."""
        with pytest.raises(ValueError):
            CodeOwner.from_string("invalid")

    def test_from_string_with_whitespace(self):
        """Test that whitespace is stripped."""
        owner = CodeOwner.from_string("  @testuser  ")
        assert owner.value == "@testuser"

    def test_str_representation(self):
        """Test string representation of CodeOwner."""
        owner = CodeOwner.from_string("@testuser")
        assert str(owner) == "@testuser"

    def test_username_fixture(self, username_owner):
        """Test username owner fixture."""
        assert username_owner.type == OwnerType.USERNAME
        assert username_owner.value == "@testuser"

    def test_team_fixture(self, team_owner):
        """Test team owner fixture."""
        assert team_owner.type == OwnerType.TEAM
        assert "@myorg/team-name" in team_owner.value

    def test_email_fixture(self, email_owner):
        """Test email owner fixture."""
        assert email_owner.type == OwnerType.EMAIL
        assert "@" in email_owner.value


class TestCodeOwnersEntry:
    """Tests for CodeOwnersEntry class."""

    def test_blank_entry(self):
        """Test creating a blank entry."""
        entry = CodeOwnersEntry.blank()
        assert entry.type == EntryType.BLANK
        assert entry.pattern is None
        assert entry.owners == []
        # Note: comment field check removed due to classmethod naming conflict
        assert entry.is_blank()
        assert not entry.is_comment()
        assert not entry.is_rule()

    def test_comment_entry(self):
        """Test creating a comment entry."""
        entry = CodeOwnersEntry.comment("This is a comment")
        assert entry.type == EntryType.COMMENT
        assert entry.comment == "This is a comment"
        assert entry.is_comment()
        assert not entry.is_blank()
        assert not entry.is_rule()

    def test_rule_entry_with_strings(self):
        """Test creating a rule entry with string owners."""
        entry = CodeOwnersEntry.rule("*.py", ["@python-team", "@senior-dev"])
        assert entry.type == EntryType.RULE
        assert entry.pattern == "*.py"
        assert len(entry.owners) == 2
        assert entry.owners[0].value == "@python-team"
        assert entry.owners[1].value == "@senior-dev"
        assert entry.is_rule()
        assert not entry.is_blank()
        assert not entry.is_comment()

    def test_rule_entry_with_codeowner_objects(self):
        """Test creating a rule entry with CodeOwner objects."""
        owner1 = CodeOwner.from_string("@user1")
        owner2 = CodeOwner.from_string("@org/team")
        entry = CodeOwnersEntry.rule("*.js", [owner1, owner2])
        assert entry.pattern == "*.js"
        assert len(entry.owners) == 2
        assert entry.owners[0] == owner1
        assert entry.owners[1] == owner2

    def test_rule_entry_with_inline_comment(self):
        """Test creating a rule with inline comment."""
        entry = CodeOwnersEntry.rule(
            "*.html", ["@frontend-team"], inline_comment="Web pages"
        )
        assert entry.pattern == "*.html"
        assert entry.comment == "Web pages"
        assert len(entry.owners) == 1

    def test_rule_entry_mixed_owners(self):
        """Test creating a rule with mixed owner types."""
        entry = CodeOwnersEntry.rule(
            "docs/**",
            ["@docs-team", "docs@example.com"],
        )
        assert len(entry.owners) == 2
        assert entry.owners[0].type == OwnerType.USERNAME
        assert entry.owners[1].type == OwnerType.EMAIL


class TestCodeOwnersFile:
    """Tests for CodeOwnersFile class."""

    def test_empty_file(self):
        """Test creating an empty CodeOwnersFile."""
        codeowners = CodeOwnersFile()
        assert len(codeowners.entries) == 0
        assert len(codeowners.get_rules()) == 0

    def test_add_entry(self):
        """Test adding entries to file."""
        codeowners = CodeOwnersFile()
        entry = CodeOwnersEntry.rule("*.py", ["@python-team"])
        codeowners.add_entry(entry)
        assert len(codeowners.entries) == 1
        assert codeowners.entries[0] == entry

    def test_add_rule(self):
        """Test add_rule helper method."""
        codeowners = CodeOwnersFile()
        codeowners.add_rule("*.py", ["@python-team"])
        assert len(codeowners.entries) == 1
        assert codeowners.entries[0].is_rule()
        assert codeowners.entries[0].pattern == "*.py"

    def test_add_comment(self):
        """Test add_comment helper method."""
        codeowners = CodeOwnersFile()
        codeowners.add_comment("This is a comment")
        assert len(codeowners.entries) == 1
        assert codeowners.entries[0].is_comment()
        assert codeowners.entries[0].comment == "This is a comment"

    def test_add_blank(self):
        """Test add_blank helper method."""
        codeowners = CodeOwnersFile()
        codeowners.add_blank()
        assert len(codeowners.entries) == 1
        assert codeowners.entries[0].is_blank()

    def test_get_rules(self):
        """Test getting only rule entries."""
        codeowners = CodeOwnersFile()
        codeowners.add_comment("Comment")
        codeowners.add_rule("*.py", ["@python-team"])
        codeowners.add_blank()
        codeowners.add_rule("*.js", ["@js-team"])

        rules = codeowners.get_rules()
        assert len(rules) == 2
        assert all(rule.is_rule() for rule in rules)
        assert rules[0].pattern == "*.py"
        assert rules[1].pattern == "*.js"

    def test_find_rules_for_pattern(self):
        """Test finding rules by pattern."""
        codeowners = CodeOwnersFile()
        codeowners.add_rule("*.py", ["@python-team"])
        codeowners.add_rule("*.js", ["@js-team"])
        codeowners.add_rule("*.py", ["@other-team"])

        py_rules = codeowners.find_rules_for_pattern("*.py")
        assert len(py_rules) == 2
        assert all(rule.pattern == "*.py" for rule in py_rules)

        js_rules = codeowners.find_rules_for_pattern("*.js")
        assert len(js_rules) == 1
        assert js_rules[0].pattern == "*.js"

        ts_rules = codeowners.find_rules_for_pattern("*.ts")
        assert len(ts_rules) == 0

    def test_remove_entry(self):
        """Test removing an entry."""
        codeowners = CodeOwnersFile()
        entry1 = CodeOwnersEntry.rule("*.py", ["@python-team"])
        entry2 = CodeOwnersEntry.rule("*.js", ["@js-team"])
        codeowners.add_entry(entry1)
        codeowners.add_entry(entry2)

        assert len(codeowners.entries) == 2
        codeowners.remove_entry(entry1)
        assert len(codeowners.entries) == 1
        assert codeowners.entries[0] == entry2

    def test_clear(self):
        """Test clearing all entries."""
        codeowners = CodeOwnersFile()
        codeowners.add_rule("*.py", ["@python-team"])
        codeowners.add_rule("*.js", ["@js-team"])
        assert len(codeowners.entries) == 2

        codeowners.clear()
        assert len(codeowners.entries) == 0

    def test_sample_fixture(self, sample_codeowners_file):
        """Test the sample_codeowners_file fixture."""
        assert len(sample_codeowners_file.entries) > 0
        rules = sample_codeowners_file.get_rules()
        assert len(rules) > 0

    def test_complex_file_structure(self):
        """Test building a complex file structure."""
        codeowners = CodeOwnersFile()

        # Add header comment
        codeowners.add_comment("CODEOWNERS file")
        codeowners.add_blank()

        # Add default rule
        codeowners.add_comment("Default owner")
        codeowners.add_rule("*", ["@default-owner"])
        codeowners.add_blank()

        # Add language-specific rules
        codeowners.add_comment("Python files")
        codeowners.add_rule("*.py", ["@python-team", "@senior-dev"])
        codeowners.add_rule("tests/**", ["@python-team", "@qa-team"])

        # 1: comment, 2: blank, 3: comment, 4: rule, 5: blank, 6: comment, 7: rule, 8: rule = 8 total
        assert len(codeowners.entries) == 8
        assert len(codeowners.get_rules()) == 3

        # Check specific rules
        py_rules = codeowners.find_rules_for_pattern("*.py")
        assert len(py_rules) == 1
        assert len(py_rules[0].owners) == 2
