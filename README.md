# github-codeowners

A Python library and CLI for parsing, validating, and managing GitHub CODEOWNERS files. Perfect for CI/CD pipelines and automation workflows.

## Features

- Parse CODEOWNERS files into structured Python objects
- Validate CODEOWNERS syntax and structure
- Programmatically add, remove, and modify ownership rules
- Command-line interface for common operations
- Support for all CODEOWNERS features:
  - Multiple owner types (@username, @org/team, email addresses)
  - Pattern-based file matching
  - Proper precedence handling

## Installation

```bash
pip install github-codeowners==0.0.3
```

For development:

```bash
git clone https://github.com/henryupton/github-codeowners.git
cd github-codeowners
pip install -e ".[dev]"
```

## Quick Start

### Command Line Usage

The `codeowners` CLI provides several commands for managing CODEOWNERS files:

```bash
# Show parsed CODEOWNERS file
codeowners show
codeowners show --repo /path/to/repo
codeowners show /path/to/CODEOWNERS

# Validate CODEOWNERS syntax
codeowners validate
codeowners validate --repo /path/to/repo

# Add a new rule
codeowners add-rule "*.py" @python-team @user1
codeowners add-rule "docs/**" @docs-team --comment "Documentation owners"

# Remove a rule
codeowners remove-rule "*.py"

# Add an owner to existing rule
codeowners add-owner "*.py" @new-maintainer

# Remove an owner from a rule
codeowners remove-owner "*.py" @old-maintainer

# Reformat the file
codeowners format
codeowners format --output CODEOWNERS.new
```

### Python API Usage

```python
from github_codeowners import (
    parse_codeowners_file,
    write_codeowners_file,
    CodeOwnersFile,
)

# Parse an existing CODEOWNERS file
codeowners = parse_codeowners_file(".github/CODEOWNERS")

# Access rules
for entry in codeowners.get_rules():
    print(f"{entry.pattern}: {[str(o) for o in entry.owners]}")

# Add a new rule
codeowners.add_rule("*.js", ["@frontend-team", "@user1"])

# Add a comment
codeowners.add_comment("Frontend code owners")

# Write back to disk
write_codeowners_file(codeowners, ".github/CODEOWNERS")
```

## CLI Commands

### `show`

Display the parsed CODEOWNERS file with line numbers and entry types.

```bash
codeowners show [FILE] [--repo PATH]
```

### `validate`

Validate the CODEOWNERS file syntax and check for common issues.

```bash
codeowners validate [FILE] [--repo PATH]
```

Exit codes:
- 0: Valid
- 1: Validation errors or file not found

### `format`

Parse and rewrite the CODEOWNERS file, normalizing formatting.

```bash
codeowners format [FILE] [--repo PATH] [--output PATH]
```

### `add-rule`

Add a new ownership rule.

```bash
codeowners add-rule PATTERN OWNERS... [FILE] [OPTIONS]

Options:
  --repo PATH        Repository root (auto-find CODEOWNERS)
  --output PATH      Output file (default: overwrite input)
  --comment TEXT     Inline comment for the rule
```

Example:
```bash
codeowners add-rule "*.py" @python-team @user1 --comment "Python files"
```

### `remove-rule`

Remove rules matching a pattern.

```bash
codeowners remove-rule PATTERN [FILE] [OPTIONS]
```

### `add-owner`

Add an owner to an existing rule.

```bash
codeowners add-owner PATTERN OWNER [FILE] [OPTIONS]
```

Example:
```bash
codeowners add-owner "*.py" @new-maintainer
```

### `remove-owner`

Remove an owner from an existing rule.

```bash
codeowners remove-owner PATTERN OWNER [FILE] [OPTIONS]
```

## Python API

### Parsing

```python
from github_codeowners import parse_codeowners, parse_codeowners_file
from github_codeowners.parser import find_codeowners_file

# Parse from string
content = "*.py @python-team\n*.js @frontend-team"
codeowners = parse_codeowners(content)

# Parse from file
codeowners = parse_codeowners_file("/path/to/CODEOWNERS")

# Auto-find CODEOWNERS in repository
codeowners_path = find_codeowners_file("/path/to/repo")
codeowners = parse_codeowners_file(codeowners_path)
```

### Creating and Modifying

```python
from github_codeowners import CodeOwnersFile, CodeOwner

# Create a new CODEOWNERS file
codeowners = CodeOwnersFile()

# Add rules
codeowners.add_rule("*.py", ["@python-team", "@user1"])
codeowners.add_rule("docs/**", ["@docs-team"])

# Add comments and blank lines
codeowners.add_blank()
codeowners.add_comment("Frontend section")
codeowners.add_rule("*.js", ["@frontend-team"])

# Find and modify rules
rules = codeowners.find_rules_for_pattern("*.py")
for rule in rules:
    # Add an owner
    rule.owners.append(CodeOwner.from_string("@new-owner"))
    # Modify inline comment
    rule.comment = "Updated comment"
```

### Writing

```python
from github_codeowners import write_codeowners, write_codeowners_file

# Write to string
content = write_codeowners(codeowners)
print(content)

# Write to file
write_codeowners_file(codeowners, ".github/CODEOWNERS")

# Create parent directories if needed
write_codeowners_file(codeowners, ".github/CODEOWNERS", create_dirs=True)
```

### Working with Entries

```python
# Iterate over all entries
for entry in codeowners.entries:
    if entry.is_rule():
        print(f"Pattern: {entry.pattern}")
        print(f"Owners: {[str(o) for o in entry.owners]}")
        if entry.comment:
            print(f"Comment: {entry.comment}")
    elif entry.is_comment():
        print(f"Comment: {entry.comment}")
    elif entry.is_blank():
        print("Blank line")

# Get only rules
rules = codeowners.get_rules()

# Find specific rules
py_rules = codeowners.find_rules_for_pattern("*.py")

# Remove entries
codeowners.remove_entry(entry)

# Clear all entries
codeowners.clear()
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Validate CODEOWNERS

on: [pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install github-codeowners
        run: pip install github-codeowners
      - name: Validate CODEOWNERS
        run: codeowners validate
```

### GitLab CI

```yaml
validate-codeowners:
  image: python:3.9
  script:
    - pip install github-codeowners
    - codeowners validate
  only:
    - merge_requests
```

### Pre-commit Hooks

This package provides pre-commit hooks for automatic validation and formatting. Add to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/henryupton/github-codeowners
    rev: v0.1.0  # Use the latest release tag
    hooks:
      # Validate CODEOWNERS syntax on every commit
      - id: validate-codeowners

      # Optional: Auto-format CODEOWNERS file
      # - id: format-codeowners

      # Optional: Check CODEOWNERS is in correct location
      # - id: check-codeowners-location
```

#### Available Hooks

**validate-codeowners**
- Validates CODEOWNERS file syntax and structure
- Checks for rules without owners
- Fails if validation errors are found

**format-codeowners**
- Automatically formats and normalizes CODEOWNERS files
- Useful for maintaining consistent formatting across your team
- Auto-fixes formatting issues

**check-codeowners-location**
- Ensures CODEOWNERS is in a valid location (`.github/`, `docs/`, or root)
- Fails if CODEOWNERS is in an invalid directory

#### Local Development Hook

For local development without installing from the repo:

```yaml
repos:
  - repo: local
    hooks:
      - id: validate-codeowners
        name: Validate CODEOWNERS
        entry: codeowners validate
        language: system
        files: (^|/)CODEOWNERS$
        pass_filenames: false
```

## CODEOWNERS Format

This library supports the full GitHub CODEOWNERS format:

- **Location**: `.github/CODEOWNERS`, `CODEOWNERS`, or `docs/CODEOWNERS`
- **Pattern syntax**: Same as `.gitignore` (with some limitations)
- **Owner types**:
  - GitHub usernames: `@username`
  - Teams: `@org/team-name`
  - Email addresses: `user@example.com`
- **Comments**: Lines starting with `#`
- **Inline comments**: `pattern @owner # comment`
- **Precedence**: Last matching pattern wins

Example CODEOWNERS file:

```
# Default owner for everything
* @default-owner

# Frontend
*.js @frontend-team
*.css @frontend-team
*.html @frontend-team

# Backend
*.py @backend-team @senior-dev

# Documentation
docs/** @docs-team @tech-writer

# CI/CD
.github/** @devops-team
```

## Development

```bash
# Clone the repository
git clone https://github.com/yourusername/github-codeowners.git
cd github-codeowners

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/ tests/

# Type checking
mypy src/
```

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Links

- [GitHub CODEOWNERS Documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
- [Issue Tracker](https://github.com/yourusername/github-codeowners/issues)