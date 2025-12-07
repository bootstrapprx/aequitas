"""Diagnostics and health check commands."""

import typer
import sys
import os
import platform
from rich.console import Console
from rich.table import Table
from typing import Optional

from app.db.session import SessionLocal
from app.core.config import settings

console = Console()
app = typer.Typer()


@app.command("health")
def health_check(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """
    Run health checks on database and system.
    """
    db = SessionLocal()
    try:
        from sqlalchemy import text

        # Test database connection
        db.execute(text("SELECT 1"))

        # Get database info
        db_result = db.execute(text("SELECT version()")).scalar()
        db_name = settings.DATABASE_URL.split("/")[-1].split("?")[0] if settings.DATABASE_URL else "unknown"

        if json_output:
            output = {
                "status": "healthy",
                "database": {
                    "connected": True,
                    "version": db_result,
                    "name": db_name,
                },
            }
            console.print_json(data=output)
        else:
            console.print("[green]✓[/green] [bold]System Health Check[/bold]")
            console.print(f"\n[cyan]Database[/cyan]")
            console.print(f"[bold]Status:[/bold] [green]Connected ✓[/green]")
            console.print(f"[bold]Name:[/bold] {db_name}")
            console.print(f"[bold]Version:[/bold] {db_result}")

        sys.exit(0)

    except Exception as e:
        if json_output:
            output = {
                "status": "unhealthy",
                "database": {
                    "connected": False,
                    "error": str(e),
                },
            }
            console.print_json(data=output)
        else:
            console.print("[red]✗[/red] [bold]System Health Check Failed[/bold]")
            console.print(f"[red]Database Error:[/red] {str(e)}")

        sys.exit(1)
    finally:
        db.close()


@app.command("version")
def version_info(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Display version information."""
    try:
        import cli
        from app import __version__ as app_version

        if json_output:
            output = {
                "cli_version": cli.__version__,
                "app_version": app_version if hasattr(sys.modules.get('app', None), '__version__') else "1.0.0",
                "python_version": platform.python_version(),
                "platform": platform.platform(),
            }
            console.print_json(data=output)
        else:
            console.print("[bold cyan]Aequitas Version Information[/bold cyan]")
            console.print(f"[bold]CLI Version:[/bold] {cli.__version__}")
            console.print(f"[bold]Python Version:[/bold] {platform.python_version()}")
            console.print(f"[bold]Platform:[/bold] {platform.platform()}")

        sys.exit(0)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}", style="bold red")
        sys.exit(1)


@app.command("env")
def env_info(
    show_secrets: bool = typer.Option(False, "--show-secrets", help="Show sensitive values (dangerous!)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Display environment configuration (safe subset)."""
    try:
        # Safe environment variables to display
        safe_vars = [
            "DATABASE_URL",
            "OLLAMA_HOST",
            "OLLAMA_MODEL",
            "CLOUDFLARE_ACCOUNT_ID",
            "QBO_CLIENT_ID",
            "VITE_API_URL",
        ]

        # Sensitive variables to mask
        sensitive_vars = [
            "SECRET_KEY",
            "DATABASE_PASSWORD",
            "CLOUDFLARE_API_TOKEN",
            "QBO_CLIENT_SECRET",
            "STRIPE_API_KEY",
        ]

        env_data = {}

        for var in safe_vars:
            value = getattr(settings, var.lower(), None) or os.getenv(var)
            if value:
                # Mask passwords in DATABASE_URL
                if "DATABASE_URL" in var and not show_secrets:
                    value = value.split("@")[1] if "@" in value else value[:20] + "..."
                env_data[var] = value

        for var in sensitive_vars:
            value = getattr(settings, var.lower(), None) or os.getenv(var)
            if value:
                env_data[var] = value if show_secrets else "***MASKED***"

        if json_output:
            console.print_json(data=env_data)
        else:
            table = Table(title="Environment Configuration")
            table.add_column("Variable", style="cyan")
            table.add_column("Value", style="green")

            for key, value in sorted(env_data.items()):
                table.add_row(key, str(value))

            console.print(table)

            if not show_secrets:
                console.print("\n[dim]Use --show-secrets to reveal sensitive values[/dim]")

        sys.exit(0)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}", style="bold red")
        sys.exit(1)
