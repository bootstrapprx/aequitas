"""Logs management commands."""

import typer
import sys
import subprocess
from rich.console import Console
from rich.table import Table
from typing import Optional
from pathlib import Path

console = Console()
app = typer.Typer()


@app.command("tail")
def tail_logs(
    lines: int = typer.Option(50, "-n", help="Number of lines to show"),
    follow: bool = typer.Option(False, "-f", help="Follow log output"),
):
    """
    Tail backend logs.

    Note: This attempts to read from common log locations.
    For containerized deployments, use `docker compose logs` instead.
    """
    try:
        # Common log file locations
        log_paths = [
            Path("backend/logs/app.log"),
            Path("backend/aequitas.log"),
            Path("/var/log/aequitas/backend.log"),
        ]

        log_file = None
        for path in log_paths:
            if path.exists():
                log_file = path
                break

        if not log_file:
            console.print("[yellow]No log file found in common locations.[/yellow]")
            console.print("[yellow]For Docker deployments, use: docker compose -f docker-compose.dev.yml logs backend[/yellow]")
            sys.exit(0)

        console.print(f"[cyan]Reading logs from {log_file}...[/cyan]\n")

        cmd = ["tail", f"-n", str(lines)]
        if follow:
            cmd.append("-f")
        cmd.append(str(log_file))

        subprocess.run(cmd)

        sys.exit(0)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}", style="bold red")
        sys.exit(1)


@app.command("session")
def session_logs(
    limit: int = typer.Option(100, "-n", help="Number of session logs to show"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Dump internal session/activity logs from database."""
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        # Try to get session logs if they exist
        from sqlalchemy import text

        query = text("""
            SELECT id, created_at, session_data
            FROM session_logs
            ORDER BY created_at DESC
            LIMIT :limit
        """)

        try:
            result = db.execute(query, {"limit": limit})
            logs = result.fetchall()

            if json_output:
                output = [
                    {
                        "id": str(row[0]),
                        "created_at": str(row[1]),
                        "session_data": row[2],
                    }
                    for row in logs
                ]
                console.print_json(data=output)
            else:
                if logs:
                    table = Table(title=f"Session Logs (Last {len(logs)})")
                    table.add_column("ID", style="dim")
                    table.add_column("Created At", style="cyan")
                    table.add_column("Data")

                    for row in logs:
                        table.add_row(
                            str(row[0])[:8] + "...",
                            str(row[1]),
                            str(row[2])[:50] + "..." if row[2] and len(str(row[2])) > 50 else str(row[2]),
                        )

                    console.print(table)
                else:
                    console.print("[yellow]No session logs found[/yellow]")

        except Exception as e:
            console.print(f"[yellow]Session logs table not found or error accessing it[/yellow]")
            console.print(f"[dim]Error: {str(e)}[/dim]")

        sys.exit(0)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}", style="bold red")
        sys.exit(1)
    finally:
        db.close()


@app.command("dump")
def dump_logs(
    output_file: str = typer.Option("logs_dump.txt", "-o", help="Output file path"),
):
    """Export logs to a file."""
    try:
        log_paths = [
            Path("backend/logs/app.log"),
            Path("backend/aequitas.log"),
        ]

        log_file = None
        for path in log_paths:
            if path.exists():
                log_file = path
                break

        if not log_file:
            console.print("[yellow]No log file found to dump[/yellow]")
            sys.exit(1)

        # Copy log file to output
        import shutil
        shutil.copy(log_file, output_file)

        console.print(f"[green]✓[/green] Logs dumped to {output_file}")
        console.print(f"[bold]Source:[/bold] {log_file}")
        console.print(f"[bold]Size:[/bold] {Path(output_file).stat().st_size} bytes")

        sys.exit(0)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}", style="bold red")
        sys.exit(1)
