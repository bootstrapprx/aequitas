"""Main Aequitas CLI application."""

import sys
from pathlib import Path

# Add backend to path for imports
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

import typer
from rich.console import Console
from typing import Optional

# Import command modules
from cli.commands import companies, groups, mappings, users, db, logs, diagnostics

# Global console for rich output
console = Console()

# Global state
class State:
    def __init__(self):
        self.debug = False
        self.json_output = False

state = State()

# Create main app
app = typer.Typer(
    name="aequitas",
    help="Aequitas CLI - Administrative and operational tool for Aequitas accounting system",
    add_completion=False,
)

# Add command groups
app.add_typer(companies.app, name="companies", help="Manage companies")
app.add_typer(groups.app, name="groups", help="Manage company groups")
app.add_typer(mappings.app, name="mappings", help="Manage account mappings")
app.add_typer(users.app, name="users", help="Manage users")
app.add_typer(db.app, name="db", help="Database operations")
app.add_typer(logs.app, name="logs", help="View and manage logs")
app.add_typer(diagnostics.app, name="diag", help="Diagnostics and health checks")


@app.callback()
def main(
    debug: bool = typer.Option(False, "--debug", help="Enable debug mode"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """
    Aequitas CLI - Administrative and operational tool

    Run 'aequitas COMMAND --help' for more information on a command.
    """
    state.debug = debug
    state.json_output = json_output

    if debug:
        console.print("[yellow]Debug mode enabled[/yellow]")


def get_state() -> State:
    """Get global CLI state."""
    return state


if __name__ == "__main__":
    app()
