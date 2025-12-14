"""Database management commands."""

import typer
import sys
import subprocess
from rich.console import Console
from rich.table import Table
from typing import Optional

from app.db.session import SessionLocal, engine
from app.db.base import Base

console = Console()
app = typer.Typer()


@app.command("upgrade")
def upgrade_db(
    revision: str = typer.Option("head", "-r", help="Revision to upgrade to"),
):
    """Run database migrations (alembic upgrade)."""
    try:
        console.print(f"[cyan]Running database upgrade to {revision}...[/cyan]")
        result = subprocess.run(
            ["alembic", "upgrade", revision],
            cwd="backend",
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            console.print("[green]✓[/green] Database upgraded successfully")
            if result.stdout:
                console.print(result.stdout)
            sys.exit(0)
        else:
            console.print(f"[red]Error upgrading database:[/red]", style="bold red")
            if result.stderr:
                console.print(result.stderr)
            sys.exit(1)

    except FileNotFoundError:
        console.print("[red]Alembic not found. Make sure alembic is installed.[/red]", style="bold red")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}", style="bold red")
        sys.exit(1)


@app.command("downgrade")
def downgrade_db(
    steps: int = typer.Option(1, "-n", help="Number of revisions to downgrade"),
):
    """Downgrade database migrations (alembic downgrade)."""
    try:
        revision = f"-{steps}" if steps > 0 else "base"
        console.print(f"[cyan]Running database downgrade ({revision})...[/cyan]")

        result = subprocess.run(
            ["alembic", "downgrade", revision],
            cwd="backend",
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            console.print("[green]✓[/green] Database downgraded successfully")
            if result.stdout:
                console.print(result.stdout)
            sys.exit(0)
        else:
            console.print(f"[red]Error downgrading database:[/red]", style="bold red")
            if result.stderr:
                console.print(result.stderr)
            sys.exit(1)

    except FileNotFoundError:
        console.print("[red]Alembic not found. Make sure alembic is installed.[/red]", style="bold red")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}", style="bold red")
        sys.exit(1)


@app.command("revision")
def create_revision(
    message: str = typer.Option(..., "-m", help="Revision message"),
    autogenerate: bool = typer.Option(True, "--autogenerate/--no-autogenerate", help="Auto-generate migration"),
):
    """Create a new database migration."""
    try:
        console.print(f"[cyan]Creating new migration: {message}...[/cyan]")

        cmd = ["alembic", "revision", "-m", message]
        if autogenerate:
            cmd.insert(2, "--autogenerate")

        result = subprocess.run(
            cmd,
            cwd="backend",
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            console.print("[green]✓[/green] Migration created successfully")
            if result.stdout:
                console.print(result.stdout)
            sys.exit(0)
        else:
            console.print(f"[red]Error creating migration:[/red]", style="bold red")
            if result.stderr:
                console.print(result.stderr)
            sys.exit(1)

    except FileNotFoundError:
        console.print("[red]Alembic not found. Make sure alembic is installed.[/red]", style="bold red")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}", style="bold red")
        sys.exit(1)


@app.command("inspect")
def inspect_db(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Inspect database tables and row counts."""
    db = SessionLocal()
    try:
        from sqlalchemy import inspect, text

        inspector = inspect(engine)
        tables = inspector.get_table_names()

        if json_output:
            output = {}
            for table_name in tables:
                try:
                    count = db.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
                    output[table_name] = count
                except Exception:
                    output[table_name] = "Error"

            console.print_json(data=output)
        else:
            table = Table(title="Database Tables")
            table.add_column("Table Name", style="cyan")
            table.add_column("Row Count", style="green", justify="right")

            total_rows = 0
            for table_name in sorted(tables):
                try:
                    count = db.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
                    table.add_row(table_name, str(count))
                    total_rows += count
                except Exception as e:
                    table.add_row(table_name, f"[red]Error[/red]")

            console.print(table)
            console.print(f"\n[bold]Total tables:[/bold] {len(tables)}")
            console.print(f"[bold]Total rows:[/bold] {total_rows}")

        sys.exit(0)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}", style="bold red")
        sys.exit(1)
    finally:
        db.close()


@app.command("seed")
def seed_db(
    master_chart: bool = typer.Option(False, "--master-chart", help="Seed master chart"),
):
    """Seed database with initial data."""
    db = SessionLocal()
    try:
        if master_chart:
            console.print("[cyan]Seeding master chart...[/cyan]")

            # Run the seed script
            result = subprocess.run(
                ["python", "app/data/seed_enriched_master_chart.py"],
                cwd="backend",
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                console.print("[green]✓[/green] Master chart seeded successfully")
                sys.exit(0)
            else:
                console.print(f"[red]Error seeding master chart:[/red]", style="bold red")
                if result.stderr:
                    console.print(result.stderr)
                sys.exit(1)
        else:
            console.print("[yellow]No seed option specified. Use --master-chart to seed master chart.[/yellow]")
            sys.exit(0)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}", style="bold red")
        sys.exit(1)
    finally:
        db.close()
