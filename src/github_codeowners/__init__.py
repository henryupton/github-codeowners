"""GitHub CODEOWNERS parser and manager."""

from .models import CodeOwner, CodeOwnersEntry, CodeOwnersFile, CodeOwnersFileSizeError
from .parser import parse_codeowners, parse_codeowners_file
from .writer import write_codeowners, write_codeowners_file

__version__ = "0.1.0"
__all__ = [
    "CodeOwner",
    "CodeOwnersEntry",
    "CodeOwnersFile",
    "CodeOwnersFileSizeError",
    "parse_codeowners",
    "parse_codeowners_file",
    "write_codeowners",
    "write_codeowners_file",
]