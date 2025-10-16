"""Pytest fixtures for github-codeowners tests."""

import tempfile
from pathlib import Path

import pytest

from github_codeowners.models import CodeOwnersFile, CodeOwner, CodeOwnersEntry


@pytest.fixture
def sample_codeowners_content():
    """Sample CODEOWNERS file content."""
    return """# Default owner
* @default-owner

# Python files
*.py @python-team @senior-dev

# Frontend
*.js @frontend-team
*.css @frontend-team
*.html @frontend-team # Web pages

# Documentation
docs/** @docs-team @tech-writer
README.md @docs-team

# CI/CD
.github/** @devops-team
"""


@pytest.fixture
def simple_codeowners_content():
    """Simple CODEOWNERS file content."""
    return """*.py @python-team
*.js @javascript-team
"""


@pytest.fixture
def complex_codeowners_content():
    """Complex CODEOWNERS file with various features."""
    return """# This is a comment
# Another comment line

# Default owner for everything
* @default-team

# Backend services
/backend/** @backend-team @tech-lead
/backend/api/** @api-team

# Frontend
/frontend/** @frontend-team
*.tsx @react-devs
*.vue @vue-devs # Vue components

# Infrastructure
/infrastructure/** @devops-team @sre-team
*.yml @devops-team
*.yaml @devops-team

# Documentation with email
docs/** @docs-team docs@example.com

# Mixed owners
/shared/** @backend-team @frontend-team @shared-services/platform
"""


@pytest.fixture
def temp_codeowners_file(tmp_path, sample_codeowners_content):
    """Create a temporary CODEOWNERS file."""
    codeowners_file = tmp_path / "CODEOWNERS"
    codeowners_file.write_text(sample_codeowners_content)
    return codeowners_file


@pytest.fixture
def temp_repo_with_codeowners(tmp_path, sample_codeowners_content):
    """Create a temporary repo with CODEOWNERS in .github/."""
    github_dir = tmp_path / ".github"
    github_dir.mkdir()
    codeowners_file = github_dir / "CODEOWNERS"
    codeowners_file.write_text(sample_codeowners_content)
    return tmp_path


@pytest.fixture
def sample_codeowners_file():
    """Create a sample CodeOwnersFile object."""
    codeowners = CodeOwnersFile()

    codeowners.add_comment("Default owner")
    codeowners.add_rule("*", ["@default-owner"])
    codeowners.add_blank()

    codeowners.add_comment("Python files")
    codeowners.add_rule("*.py", ["@python-team", "@senior-dev"])
    codeowners.add_blank()

    codeowners.add_comment("Frontend")
    codeowners.add_rule("*.js", ["@frontend-team"])
    codeowners.add_rule("*.css", ["@frontend-team"])
    codeowners.add_rule("*.html", ["@frontend-team"], inline_comment="Web pages")

    return codeowners


@pytest.fixture
def username_owner():
    """Sample username owner."""
    return CodeOwner.from_string("@testuser")


@pytest.fixture
def team_owner():
    """Sample team owner."""
    return CodeOwner.from_string("@myorg/team-name")


@pytest.fixture
def email_owner():
    """Sample email owner."""
    return CodeOwner.from_string("user@example.com")
