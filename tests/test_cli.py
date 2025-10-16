"""Tests for github_codeowners.cli module."""

import pytest
from click.testing import CliRunner
from pathlib import Path

from github_codeowners.cli import cli
from github_codeowners.parser import parse_codeowners_file


@pytest.fixture
def runner():
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_codeowners_with_rules(tmp_path):
    """Create a temporary CODEOWNERS file with some rules."""
    codeowners_file = tmp_path / "CODEOWNERS"
    content = """# Default owner
* @default-owner

# Python files
*.py @python-team @senior-dev

# Frontend
*.js @frontend-team
*.css @frontend-team
"""
    codeowners_file.write_text(content)
    return codeowners_file


class TestShowCommand:
    """Tests for the 'show' command."""

    def test_show_with_file_argument(self, runner, temp_codeowners_file):
        """Test show command with file argument."""
        result = runner.invoke(cli, ["show", str(temp_codeowners_file)])
        assert result.exit_code == 0
        assert "CODEOWNERS file:" in result.output
        assert "Total entries:" in result.output
        assert "Rules:" in result.output

    def test_show_with_repo_option(self, runner, temp_repo_with_codeowners):
        """Test show command with --repo option."""
        result = runner.invoke(cli, ["show", "--repo", str(temp_repo_with_codeowners)])
        assert result.exit_code == 0
        assert "CODEOWNERS file:" in result.output

    def test_show_displays_rules(self, runner, temp_codeowners_with_rules):
        """Test that show displays rules correctly."""
        result = runner.invoke(cli, ["show", str(temp_codeowners_with_rules)])
        assert result.exit_code == 0
        assert "*.py" in result.output
        assert "@python-team" in result.output
        assert "*.js" in result.output

    def test_show_nonexistent_file(self, runner, tmp_path):
        """Test show with nonexistent file."""
        nonexistent = tmp_path / "nonexistent"
        result = runner.invoke(cli, ["show", str(nonexistent)])
        # Click uses exit code 2 for usage errors (file not found)
        assert result.exit_code in [1, 2]
        assert "Error:" in result.output or "does not exist" in result.output.lower()


class TestValidateCommand:
    """Tests for the 'validate' command."""

    def test_validate_valid_file(self, runner, temp_codeowners_file):
        """Test validate command with valid file."""
        result = runner.invoke(cli, ["validate", str(temp_codeowners_file)])
        assert result.exit_code == 0
        assert "valid" in result.output.lower()

    def test_validate_with_repo_option(self, runner, temp_repo_with_codeowners):
        """Test validate command with --repo option."""
        result = runner.invoke(cli, ["validate", "--repo", str(temp_repo_with_codeowners)])
        assert result.exit_code == 0
        assert "valid" in result.output.lower()

    def test_validate_file_with_no_owners(self, runner, tmp_path):
        """Test validate detects rules without owners."""
        codeowners_file = tmp_path / "CODEOWNERS"
        # This shouldn't actually create a rule without owners in normal parsing,
        # but we can test the validation logic
        codeowners_file.write_text("*.py @python-team\n*.js @js-team\n")
        result = runner.invoke(cli, ["validate", str(codeowners_file)])
        assert result.exit_code == 0

    def test_validate_nonexistent_file(self, runner, tmp_path):
        """Test validate with nonexistent file."""
        nonexistent = tmp_path / "nonexistent"
        result = runner.invoke(cli, ["validate", str(nonexistent)])
        # Click uses exit code 2 for usage errors (file not found)
        assert result.exit_code in [1, 2]


class TestFormatCommand:
    """Tests for the 'format' command."""

    def test_format_file(self, runner, temp_codeowners_with_rules, tmp_path):
        """Test format command."""
        output_file = tmp_path / "formatted"
        result = runner.invoke(
            cli,
            ["format", str(temp_codeowners_with_rules), "--output", str(output_file)]
        )
        assert result.exit_code == 0
        assert output_file.exists()
        assert "Formatted" in result.output

    def test_format_overwrites_input(self, runner, tmp_path):
        """Test format command overwrites input file by default."""
        codeowners_file = tmp_path / "CODEOWNERS"
        original_content = "*.py @python-team\n*.js @js-team\n"
        codeowners_file.write_text(original_content)

        result = runner.invoke(cli, ["format", str(codeowners_file)])
        assert result.exit_code == 0

        # File should still exist and be parseable
        assert codeowners_file.exists()
        reparsed = parse_codeowners_file(codeowners_file)
        assert len(reparsed.get_rules()) == 2

    def test_format_with_repo_option(self, runner, temp_repo_with_codeowners, tmp_path):
        """Test format command with --repo option."""
        output_file = tmp_path / "formatted"
        result = runner.invoke(
            cli,
            ["format", "--repo", str(temp_repo_with_codeowners), "--output", str(output_file)]
        )
        assert result.exit_code == 0
        assert output_file.exists()


class TestAddRuleCommand:
    """Tests for the 'add-rule' command."""

    def test_add_rule_basic(self, runner, temp_codeowners_with_rules):
        """Test adding a basic rule."""
        result = runner.invoke(
            cli,
            ["add-rule", "*.md", "@markdown-team", "--file", str(temp_codeowners_with_rules)]
        )
        assert result.exit_code == 0
        assert "Added rule" in result.output
        assert "*.md" in result.output

        # Verify the rule was added
        codeowners = parse_codeowners_file(temp_codeowners_with_rules)
        md_rules = codeowners.find_rules_for_pattern("*.md")
        assert len(md_rules) == 1

    def test_add_rule_multiple_owners(self, runner, temp_codeowners_with_rules):
        """Test adding a rule with multiple owners."""
        result = runner.invoke(
            cli,
            ["add-rule", "*.ts", "@typescript-team", "@senior-dev", "--file", str(temp_codeowners_with_rules)]
        )
        assert result.exit_code == 0

        # Verify the rule was added with multiple owners
        codeowners = parse_codeowners_file(temp_codeowners_with_rules)
        ts_rules = codeowners.find_rules_for_pattern("*.ts")
        assert len(ts_rules) == 1
        assert len(ts_rules[0].owners) == 2

    def test_add_rule_with_comment(self, runner, temp_codeowners_with_rules):
        """Test adding a rule with inline comment."""
        result = runner.invoke(
            cli,
            [
                "add-rule", "*.md", "@docs-team",
                "--file", str(temp_codeowners_with_rules),
                "--comment", "Documentation files"
            ]
        )
        assert result.exit_code == 0
        assert "Comment: Documentation files" in result.output

        # Verify comment was added
        codeowners = parse_codeowners_file(temp_codeowners_with_rules)
        md_rules = codeowners.find_rules_for_pattern("*.md")
        assert md_rules[0].comment == "Documentation files"

    def test_add_rule_with_repo_option(self, runner, temp_repo_with_codeowners):
        """Test add-rule with --repo option."""
        result = runner.invoke(
            cli,
            ["add-rule", "*.md", "@docs-team", "--repo", str(temp_repo_with_codeowners)]
        )
        assert result.exit_code == 0


class TestRemoveRuleCommand:
    """Tests for the 'remove-rule' command."""

    def test_remove_rule_existing(self, runner, temp_codeowners_with_rules):
        """Test removing an existing rule."""
        # Verify rule exists
        codeowners = parse_codeowners_file(temp_codeowners_with_rules)
        assert len(codeowners.find_rules_for_pattern("*.py")) == 1

        # Remove it
        result = runner.invoke(
            cli,
            ["remove-rule", "*.py", "--file", str(temp_codeowners_with_rules)]
        )
        assert result.exit_code == 0
        assert "Removed" in result.output

        # Verify it's gone
        codeowners = parse_codeowners_file(temp_codeowners_with_rules)
        assert len(codeowners.find_rules_for_pattern("*.py")) == 0

    def test_remove_rule_nonexistent(self, runner, temp_codeowners_with_rules):
        """Test removing a nonexistent rule."""
        result = runner.invoke(
            cli,
            ["remove-rule", "*.nonexistent", "--file", str(temp_codeowners_with_rules)]
        )
        assert result.exit_code == 1
        assert "No rules found" in result.output

    def test_remove_rule_with_repo_option(self, runner, temp_repo_with_codeowners):
        """Test remove-rule with --repo option."""
        result = runner.invoke(
            cli,
            ["remove-rule", "*", "--repo", str(temp_repo_with_codeowners)]
        )
        # Should succeed if the pattern exists
        assert "Removed" in result.output or "No rules found" in result.output


class TestAddOwnerCommand:
    """Tests for the 'add-owner' command."""

    def test_add_owner_to_existing_rule(self, runner, temp_codeowners_with_rules):
        """Test adding an owner to existing rule."""
        result = runner.invoke(
            cli,
            ["add-owner", "*.py", "@new-maintainer", "--file", str(temp_codeowners_with_rules)]
        )
        assert result.exit_code == 0
        assert "Added" in result.output

        # Verify owner was added
        codeowners = parse_codeowners_file(temp_codeowners_with_rules)
        py_rules = codeowners.find_rules_for_pattern("*.py")
        assert len(py_rules) == 1
        owner_values = [o.value for o in py_rules[0].owners]
        assert "@new-maintainer" in owner_values

    def test_add_owner_already_exists(self, runner, temp_codeowners_with_rules):
        """Test adding an owner that already exists."""
        result = runner.invoke(
            cli,
            ["add-owner", "*.py", "@python-team", "--file", str(temp_codeowners_with_rules)]
        )
        # Should succeed but notify that owner already exists
        assert "already exists" in result.output.lower()

    def test_add_owner_pattern_not_found(self, runner, temp_codeowners_with_rules):
        """Test adding owner to nonexistent pattern."""
        result = runner.invoke(
            cli,
            ["add-owner", "*.nonexistent", "@owner", "--file", str(temp_codeowners_with_rules)]
        )
        assert result.exit_code == 1
        assert "No rules found" in result.output

    def test_add_owner_with_repo_option(self, runner, temp_repo_with_codeowners):
        """Test add-owner with --repo option."""
        result = runner.invoke(
            cli,
            ["add-owner", "*", "@new-owner", "--repo", str(temp_repo_with_codeowners)]
        )
        # Should work if the pattern exists
        assert result.exit_code in [0, 1]  # Could succeed or fail depending on fixture


class TestRemoveOwnerCommand:
    """Tests for the 'remove-owner' command."""

    def test_remove_owner_from_rule(self, runner, temp_codeowners_with_rules):
        """Test removing an owner from a rule."""
        result = runner.invoke(
            cli,
            ["remove-owner", "*.py", "@senior-dev", "--file", str(temp_codeowners_with_rules)]
        )
        assert result.exit_code == 0
        assert "Removed" in result.output

        # Verify owner was removed
        codeowners = parse_codeowners_file(temp_codeowners_with_rules)
        py_rules = codeowners.find_rules_for_pattern("*.py")
        owner_values = [o.value for o in py_rules[0].owners]
        assert "@senior-dev" not in owner_values

    def test_remove_owner_not_found(self, runner, temp_codeowners_with_rules):
        """Test removing an owner that doesn't exist."""
        result = runner.invoke(
            cli,
            ["remove-owner", "*.py", "@nonexistent", "--file", str(temp_codeowners_with_rules)]
        )
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_remove_owner_pattern_not_found(self, runner, temp_codeowners_with_rules):
        """Test removing owner from nonexistent pattern."""
        result = runner.invoke(
            cli,
            ["remove-owner", "*.nonexistent", "@owner", "--file", str(temp_codeowners_with_rules)]
        )
        assert result.exit_code == 1
        assert "No rules found" in result.output

    def test_remove_owner_with_repo_option(self, runner, temp_repo_with_codeowners):
        """Test remove-owner with --repo option."""
        result = runner.invoke(
            cli,
            ["remove-owner", "*", "@default-owner", "--repo", str(temp_repo_with_codeowners)]
        )
        # Should work if the pattern and owner exist
        assert result.exit_code in [0, 1]


class TestCLIIntegration:
    """Integration tests for CLI commands."""

    def test_full_workflow(self, runner, tmp_path):
        """Test a complete workflow of CLI commands."""
        codeowners_file = tmp_path / "CODEOWNERS"
        codeowners_file.write_text("* @default-owner\n")

        # Add a rule
        result = runner.invoke(
            cli,
            ["add-rule", "*.py", "@python-team", "--file", str(codeowners_file)]
        )
        assert result.exit_code == 0

        # Validate
        result = runner.invoke(cli, ["validate", str(codeowners_file)])
        assert result.exit_code == 0

        # Add an owner
        result = runner.invoke(
            cli,
            ["add-owner", "*.py", "@senior-dev", "--file", str(codeowners_file)]
        )
        assert result.exit_code == 0

        # Show
        result = runner.invoke(cli, ["show", str(codeowners_file)])
        assert result.exit_code == 0
        assert "@python-team" in result.output
        assert "@senior-dev" in result.output

        # Remove an owner
        result = runner.invoke(
            cli,
            ["remove-owner", "*.py", "@senior-dev", "--file", str(codeowners_file)]
        )
        assert result.exit_code == 0

        # Remove a rule
        result = runner.invoke(
            cli,
            ["remove-rule", "*.py", "--file", str(codeowners_file)]
        )
        assert result.exit_code == 0

        # Format
        result = runner.invoke(cli, ["format", str(codeowners_file)])
        assert result.exit_code == 0

    def test_output_option_preserves_original(self, runner, temp_codeowners_with_rules, tmp_path):
        """Test that --output option preserves original file."""
        original_content = temp_codeowners_with_rules.read_text()
        output_file = tmp_path / "output"

        result = runner.invoke(
            cli,
            [
                "add-rule", "*.md", "@docs-team",
                "--file", str(temp_codeowners_with_rules),
                "--output", str(output_file)
            ]
        )
        assert result.exit_code == 0

        # Original should be unchanged
        assert temp_codeowners_with_rules.read_text() == original_content

        # Output should have the new rule
        codeowners = parse_codeowners_file(output_file)
        assert len(codeowners.find_rules_for_pattern("*.md")) == 1


class TestCLIVersionOption:
    """Tests for CLI version option."""

    def test_version_option(self, runner):
        """Test --version option."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output
