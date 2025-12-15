"""User management commands."""

import typer
import sys
from rich.console import Console
from rich.table import Table
from typing import Optional
from uuid import UUID

from app.db.session import SessionLocal
from app.db.models.user import User
from app.core.security import get_password_hash

console = Console()
app = typer.Typer()


@app.command("list")
def list_users(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """List all users."""
    db = SessionLocal()
    try:
        users = db.query(User).all()

        if json_output:
            output = [
                {
                    "id": str(u.id),
                    "email": u.email,
                    "is_superuser": u.is_superuser,
                    "is_active": u.is_active,
                    "role": u.role,
                }
                for u in users
            ]
            console.print_json(data=output)
        else:
            table = Table(title="Users")
            table.add_column("Email", style="cyan")
            table.add_column("Role", style="green")
            table.add_column("Superuser")
            table.add_column("Status")
            table.add_column("ID", style="dim")

            for user in users:
                su_mark = "[red]✓[/red]" if user.is_superuser else ""
                status = "[green]Active[/green]" if user.is_active else "[red]Inactive[/red]"
                table.add_row(
                    user.email,
                    user.role or "USER",
                    su_mark,
                    status,
                    str(user.id)[:8] + "...",
                )

            console.print(table)
            console.print(f"\n[bold]Total:[/bold] {len(users)} users")

        sys.exit(0)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}", style="bold red")
        sys.exit(1)
    finally:
        db.close()


@app.command("create")
def create_user(
    email: str = typer.Option(..., "-e", help="User email"),
    password: str = typer.Option(..., "-p", help="User password"),
    superuser: bool = typer.Option(False, "--su", help="Make user a superuser"),
    role: str = typer.Option("USER", "-r", help="User role (USER, ACCOUNTANT, ADMIN, SU)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Create a new user."""
    db = SessionLocal()
    try:
        # Check if user exists
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            console.print(f"[red]User with email '{email}' already exists[/red]", style="bold red")
            sys.exit(1)

        # Create user
        user = User(
            email=email,
            hashed_password=get_password_hash(password),
            is_superuser=superuser,
            is_active=True,
            role=role,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        if json_output:
            output = {
                "id": str(user.id),
                "email": user.email,
                "is_superuser": user.is_superuser,
                "role": user.role,
            }
            console.print_json(data=output)
        else:
            console.print(f"[green]✓[/green] User created successfully")
            console.print(f"[bold]Email:[/bold] {user.email}")
            console.print(f"[bold]Role:[/bold] {user.role}")
            console.print(f"[bold]Superuser:[/bold] {'Yes' if user.is_superuser else 'No'}")
            console.print(f"[bold]ID:[/bold] {user.id}")

        sys.exit(0)

    except Exception as e:
        console.print(f"[red]Error creating user:[/red] {str(e)}", style="bold red")
        sys.exit(1)
    finally:
        db.close()


@app.command("info")
def user_info(
    user_id: str = typer.Argument(..., help="User ID or email"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Get detailed information about a user."""
    db = SessionLocal()
    try:
        # Try as email first
        user = db.query(User).filter(User.email == user_id).first()

        # If not found, try as UUID
        if not user:
            try:
                user = db.query(User).filter(User.id == UUID(user_id)).first()
            except ValueError:
                pass

        if not user:
            console.print(f"[red]User not found:[/red] {user_id}", style="bold red")
            sys.exit(1)

        if json_output:
            output = {
                "id": str(user.id),
                "email": user.email,
                "is_superuser": user.is_superuser,
                "is_active": user.is_active,
                "role": user.role,
                "user_uid": user.user_uid,
            }
            console.print_json(data=output)
        else:
            console.print(f"\n[bold cyan]User Information[/bold cyan]")
            console.print(f"[bold]Email:[/bold] {user.email}")
            console.print(f"[bold]ID:[/bold] {user.id}")
            console.print(f"[bold]Role:[/bold] {user.role or 'USER'}")
            console.print(f"[bold]Superuser:[/bold] {'Yes' if user.is_superuser else 'No'}")
            console.print(f"[bold]Status:[/bold] {'Active' if user.is_active else 'Inactive'}")

            # Get company associations
            company_count = len(user.user_companies) if user.user_companies else 0
            console.print(f"[bold]Companies:[/bold] {company_count}")

        sys.exit(0)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}", style="bold red")
        sys.exit(1)
    finally:
        db.close()
