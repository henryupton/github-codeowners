"""Command-line interface for managing CODEOWNERS files."""

import sys
from pathlib import Path
from typing import Optional

import click

from .models import CodeOwner, CodeOwnersFileSizeError
from .parser import parse_codeowners_file, find_codeowners_file
from .writer import write_codeowners_file, write_codeowners


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """GitHub CODEOWNERS file parser and manager.

    Parse, validate, and modify CODEOWNERS files for use in CI pipelines.
    """
    pass


@cli.command()
@click.argument("file", type=click.Path(exists=True), required=False)
@click.option("--repo", "-r", type=click.Path(exists=True), help="Repository root (auto-find CODEOWNERS)")
def show(file: Optional[str], repo: Optional[str]):
    """Display the parsed CODEOWNERS file.

    Either specify a FILE path or use --repo to auto-find the CODEOWNERS file.
    """
    try:
        file_path = _get_codeowners_path(file, repo)
        codeowners = parse_codeowners_file(file_path)

        click.echo(f"CODEOWNERS file: {file_path}")
        click.echo(f"Total entries: {len(codeowners.entries)}")
        click.echo(f"Rules: {len(codeowners.get_rules())}")
        click.echo()

        for i, entry in enumerate(codeowners.entries, 1):
            if entry.is_blank():
                click.echo(f"{i:3d}: [blank]")
            elif entry.is_comment():
                click.echo(f"{i:3d}: # {entry.comment}")
            elif entry.is_rule():
                owners_str = " ".join(str(o) for o in entry.owners)
                line = f"{i:3d}: {entry.pattern} {owners_str}"
                if entry.comment:
                    line += f" # {entry.comment}"
                click.echo(line)

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("file", type=click.Path(exists=True), required=False)
@click.option("--repo", "-r", type=click.Path(exists=True), help="Repository root (auto-find CODEOWNERS)")
def validate(file: Optional[str], repo: Optional[str]):
    """Validate the syntax of a CODEOWNERS file.

    Either specify a FILE path or use --repo to auto-find the CODEOWNERS file.
    """
    try:
        file_path = _get_codeowners_path(file, repo)
        codeowners = parse_codeowners_file(file_path)

        rules = codeowners.get_rules()
        errors = []

        # Check for rules without owners
        for entry in rules:
            if not entry.owners:
                errors.append(f"Rule '{entry.pattern}' has no owners")

        if errors:
            click.echo("Validation errors found:", err=True)
            for error in errors:
                click.echo(f"  - {error}", err=True)
            sys.exit(1)
        else:
            click.echo(f"✓ CODEOWNERS file is valid ({len(rules)} rules)")

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Parse error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("file", type=click.Path(exists=True), required=False)
@click.option("--repo", "-r", type=click.Path(exists=True), help="Repository root (auto-find CODEOWNERS)")
@click.option("--output", "-o", type=click.Path(), help="Output file (default: overwrite input)")
def format(file: Optional[str], repo: Optional[str], output: Optional[str]):
    """Reformat a CODEOWNERS file (parse and rewrite).

    Either specify a FILE path or use --repo to auto-find the CODEOWNERS file.
    """
    try:
        file_path = _get_codeowners_path(file, repo)
        codeowners = parse_codeowners_file(file_path)

        output_path = Path(output) if output else file_path
        write_codeowners_file(codeowners, output_path)

        click.echo(f"✓ Formatted CODEOWNERS file written to {output_path}")

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except CodeOwnersFileSizeError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("pattern")
@click.argument("owners", nargs=-1, required=True)
@click.option("--file", "-f", type=click.Path(exists=True), help="Path to CODEOWNERS file")
@click.option("--repo", "-r", type=click.Path(exists=True), help="Repository root (auto-find CODEOWNERS)")
@click.option("--output", "-o", type=click.Path(), help="Output file (default: overwrite input)")
@click.option("--comment", "-c", help="Inline comment for the rule")
def add_rule(pattern: str, owners: tuple, file: Optional[str], repo: Optional[str], output: Optional[str], comment: Optional[str]):
    """Add a new rule to the CODEOWNERS file.

    PATTERN: File pattern (e.g., *.py, /docs/, src/**/*.js)
    OWNERS: One or more owners (@username, @org/team, or email@example.com)

    Example: codeowners add-rule "*.py" @python-team @user1
    """
    try:
        file_path = _get_codeowners_path(file, repo)
        codeowners = parse_codeowners_file(file_path)

        # Add the new rule
        codeowners.add_rule(pattern, list(owners), comment)

        output_path = Path(output) if output else file_path
        write_codeowners_file(codeowners, output_path)

        owners_str = " ".join(owners)
        click.echo(f"✓ Added rule: {pattern} {owners_str}")
        if comment:
            click.echo(f"  Comment: {comment}")

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except CodeOwnersFileSizeError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("pattern")
@click.option("--file", "-f", type=click.Path(exists=True), help="Path to CODEOWNERS file")
@click.option("--repo", "-r", type=click.Path(exists=True), help="Repository root (auto-find CODEOWNERS)")
@click.option("--output", "-o", type=click.Path(), help="Output file (default: overwrite input)")
def remove_rule(pattern: str, file: Optional[str], repo: Optional[str], output: Optional[str]):
    """Remove a rule from the CODEOWNERS file.

    PATTERN: File pattern to remove

    Example: codeowners remove-rule "*.py"
    """
    try:
        file_path = _get_codeowners_path(file, repo)
        codeowners = parse_codeowners_file(file_path)

        # Find and remove matching rules
        matching_rules = codeowners.find_rules_for_pattern(pattern)

        if not matching_rules:
            click.echo(f"No rules found matching pattern: {pattern}", err=True)
            sys.exit(1)

        for rule in matching_rules:
            codeowners.remove_entry(rule)

        output_path = Path(output) if output else file_path
        write_codeowners_file(codeowners, output_path)

        click.echo(f"✓ Removed {len(matching_rules)} rule(s) matching: {pattern}")

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except CodeOwnersFileSizeError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("pattern")
@click.argument("owner")
@click.option("--file", "-f", type=click.Path(exists=True), help="Path to CODEOWNERS file")
@click.option("--repo", "-r", type=click.Path(exists=True), help="Repository root (auto-find CODEOWNERS)")
@click.option("--output", "-o", type=click.Path(), help="Output file (default: overwrite input)")
def add_owner(pattern: str, owner: str, file: Optional[str], repo: Optional[str], output: Optional[str]):
    """Add an owner to an existing rule.

    PATTERN: File pattern to modify
    OWNER: Owner to add (@username, @org/team, or email@example.com)

    Example: codeowners add-owner "*.py" @new-maintainer
    """
    try:
        file_path = _get_codeowners_path(file, repo)
        codeowners = parse_codeowners_file(file_path)

        # Find matching rules
        matching_rules = codeowners.find_rules_for_pattern(pattern)

        if not matching_rules:
            click.echo(f"No rules found matching pattern: {pattern}", err=True)
            sys.exit(1)

        # Add owner to each matching rule
        new_owner = CodeOwner.from_string(owner)
        modified_count = 0

        for rule in matching_rules:
            # Check if owner already exists
            if any(o.value == new_owner.value for o in rule.owners):
                click.echo(f"Owner {owner} already exists for pattern {pattern}")
            else:
                rule.owners.append(new_owner)
                modified_count += 1

        if modified_count > 0:
            output_path = Path(output) if output else file_path
            write_codeowners_file(codeowners, output_path)
            click.echo(f"✓ Added {owner} to {modified_count} rule(s) matching: {pattern}")

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except CodeOwnersFileSizeError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("pattern")
@click.argument("owner")
@click.option("--file", "-f", type=click.Path(exists=True), help="Path to CODEOWNERS file")
@click.option("--repo", "-r", type=click.Path(exists=True), help="Repository root (auto-find CODEOWNERS)")
@click.option("--output", "-o", type=click.Path(), help="Output file (default: overwrite input)")
def remove_owner(pattern: str, owner: str, file: Optional[str], repo: Optional[str], output: Optional[str]):
    """Remove an owner from an existing rule.

    PATTERN: File pattern to modify
    OWNER: Owner to remove (@username, @org/team, or email@example.com)

    Example: codeowners remove-owner "*.py" @old-maintainer
    """
    try:
        file_path = _get_codeowners_path(file, repo)
        codeowners = parse_codeowners_file(file_path)

        # Find matching rules
        matching_rules = codeowners.find_rules_for_pattern(pattern)

        if not matching_rules:
            click.echo(f"No rules found matching pattern: {pattern}", err=True)
            sys.exit(1)

        # Remove owner from each matching rule
        modified_count = 0

        for rule in matching_rules:
            original_count = len(rule.owners)
            rule.owners = [o for o in rule.owners if o.value != owner]
            if len(rule.owners) < original_count:
                modified_count += 1

        if modified_count > 0:
            output_path = Path(output) if output else file_path
            write_codeowners_file(codeowners, output_path)
            click.echo(f"✓ Removed {owner} from {modified_count} rule(s) matching: {pattern}")
        else:
            click.echo(f"Owner {owner} not found in any rules matching: {pattern}", err=True)
            sys.exit(1)

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except CodeOwnersFileSizeError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def _get_codeowners_path(file: Optional[str], repo: Optional[str]) -> Path:
    """Get the CODEOWNERS file path from either explicit path or repo root.

    Args:
        file: Explicit file path
        repo: Repository root path

    Returns:
        Path to CODEOWNERS file

    Raises:
        FileNotFoundError: If file cannot be found
    """
    if file:
        return Path(file)
    elif repo:
        return find_codeowners_file(repo)
    else:
        # Try current directory
        try:
            return find_codeowners_file(".")
        except FileNotFoundError:
            raise FileNotFoundError(
                "No CODEOWNERS file specified. Use FILE argument, --repo option, "
                "or run from a repository root."
            )


if __name__ == "__main__":
    cli()