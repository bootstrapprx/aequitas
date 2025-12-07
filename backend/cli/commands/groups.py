"""GroupCompany management commands."""

import typer
import sys
from rich.console import Console
from rich.table import Table
from typing import Optional
from uuid import UUID

from app.db.session import SessionLocal
from app.services.group_service import GroupService

console = Console()
app = typer.Typer()


@app.command("list")
def list_groups(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """List all company groups."""
    db = SessionLocal()
    try:
        # Get all groups (in real scenario, might filter by user)
        from app.db.models.group_company import GroupCompany
        groups = db.query(GroupCompany).all()

        if json_output:
            output = [
                {
                    "id": str(g.id),
                    "name": g.name,
                    "description": g.description,
                    "owner_user_id": str(g.owner_user_id),
                    "created_at": g.created_at.isoformat() if g.created_at else None,
                }
                for g in groups
            ]
            console.print_json(data=output)
        else:
            table = Table(title="Company Groups")
            table.add_column("Name", style="cyan")
            table.add_column("Description")
            table.add_column("ID", style="dim")

            for group in groups:
                table.add_row(
                    group.name,
                    group.description or "-",
                    str(group.id)[:8] + "...",
                )

            console.print(table)
            console.print(f"\n[bold]Total:[/bold] {len(groups)} groups")

        sys.exit(0)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}", style="bold red")
        sys.exit(1)
    finally:
        db.close()


@app.command("create")
def create_group(
    name: str = typer.Argument(..., help="Group name"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Group description"),
    owner_user_id: Optional[str] = typer.Option(None, "--owner", help="Owner user ID (defaults to first superuser)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Create a new company group."""
    db = SessionLocal()
    try:
        # Get owner user ID
        if not owner_user_id:
            # Default to first superuser
            from app.db.models.user import User
            superuser = db.query(User).filter(User.is_superuser == True).first()
            if not superuser:
                console.print("[red]No superuser found. Please specify --owner[/red]", style="bold red")
                sys.exit(1)
            owner_user_id = str(superuser.id)

        group = GroupService.create_group(
            db=db,
            name=name,
            description=description,
            owner_user_id=UUID(owner_user_id),
        )

        if json_output:
            output = {
                "id": str(group.id),
                "name": group.name,
                "description": group.description,
                "owner_user_id": str(group.owner_user_id),
            }
            console.print_json(data=output)
        else:
            console.print(f"[green]✓[/green] Group created successfully")
            console.print(f"[bold]Name:[/bold] {group.name}")
            console.print(f"[bold]ID:[/bold] {group.id}")

        sys.exit(0)

    except Exception as e:
        console.print(f"[red]Error creating group:[/red] {str(e)}", style="bold red")
        sys.exit(1)
    finally:
        db.close()


@app.command("info")
def group_info(
    group_id: str = typer.Argument(..., help="Group ID"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Get detailed information about a group including member companies."""
    db = SessionLocal()
    try:
        group = GroupService.get_group_by_id(db, UUID(group_id))

        if not group:
            console.print(f"[red]Group not found:[/red] {group_id}", style="bold red")
            sys.exit(1)

        companies = GroupService.get_group_companies(db, UUID(group_id))

        if json_output:
            output = {
                "id": str(group.id),
                "name": group.name,
                "description": group.description,
                "owner_user_id": str(group.owner_user_id),
                "companies": [
                    {
                        "id": str(c.id),
                        "name": c.name,
                        "ucid": c.ucid,
                        "is_active": c.is_active,
                    }
                    for c in companies
                ],
            }
            console.print_json(data=output)
        else:
            console.print(f"\n[bold cyan]Group Information[/bold cyan]")
            console.print(f"[bold]Name:[/bold] {group.name}")
            console.print(f"[bold]ID:[/bold] {group.id}")
            if group.description:
                console.print(f"[bold]Description:[/bold] {group.description}")

            console.print(f"\n[bold cyan]Member Companies ({len(companies)})[/bold cyan]")
            if companies:
                table = Table(show_header=True)
                table.add_column("UCID", style="cyan")
                table.add_column("Name", style="green")
                table.add_column("Status")

                for company in companies:
                    status = "[green]✓ Active[/green]" if company.is_active else "[red]✗ Inactive[/red]"
                    table.add_row(company.ucid, company.name, status)

                console.print(table)
            else:
                console.print("[dim]No companies in this group[/dim]")

        sys.exit(0)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}", style="bold red")
        sys.exit(1)
    finally:
        db.close()


@app.command("add-company")
def add_company(
    group_id: str = typer.Argument(..., help="Group ID"),
    company_id: str = typer.Argument(..., help="Company ID or UCID"),
):
    """Add a company to a group."""
    db = SessionLocal()
    try:
        # Resolve company ID
        from app.services.company_service import CompanyService
        company = CompanyService.get_company_by_ucid(db, company_id)
        if not company:
            try:
                company = CompanyService.get_company_by_id(db, UUID(company_id))
            except ValueError:
                pass

        if not company:
            console.print(f"[red]Company not found:[/red] {company_id}", style="bold red")
            sys.exit(1)

        GroupService.add_company_to_group(db, UUID(group_id), company.id)

        console.print(f"[green]✓[/green] Company '{company.name}' added to group successfully")
        sys.exit(0)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}", style="bold red")
        sys.exit(1)
    finally:
        db.close()


@app.command("remove-company")
def remove_company(
    group_id: str = typer.Argument(..., help="Group ID"),
    company_id: str = typer.Argument(..., help="Company ID or UCID"),
):
    """Remove a company from a group."""
    db = SessionLocal()
    try:
        # Resolve company ID
        from app.services.company_service import CompanyService
        company = CompanyService.get_company_by_ucid(db, company_id)
        if not company:
            try:
                company = CompanyService.get_company_by_id(db, UUID(company_id))
            except ValueError:
                pass

        if not company:
            console.print(f"[red]Company not found:[/red] {company_id}", style="bold red")
            sys.exit(1)

        success = GroupService.remove_company_from_group(db, UUID(group_id), company.id)

        if success:
            console.print(f"[green]✓[/green] Company '{company.name}' removed from group successfully")
            sys.exit(0)
        else:
            console.print(f"[yellow]Company was not a member of this group[/yellow]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}", style="bold red")
        sys.exit(1)
    finally:
        db.close()
