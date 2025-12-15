"""Companies management commands."""

import typer
import json
import sys
from rich.console import Console
from rich.table import Table
from typing import Optional
from uuid import UUID

from app.db.session import SessionLocal
from app.services.company_service import CompanyService
from app.schemas.company import CompanyCreate
from app.db.models.company import SubscriptionType

console = Console()
app = typer.Typer()


@app.command("list")
def list_companies(
    status: str = typer.Option("active", help="Filter by status: active, inactive, all"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """List all companies."""
    db = SessionLocal()
    try:
        active_only = status == "active"
        if status == "inactive":
            companies = [c for c in CompanyService.get_all_companies(db, active_only=False) if not c.is_active]
        else:
            companies = CompanyService.get_all_companies(db, active_only=active_only)

        if json_output:
            output = [
                {
                    "id": str(c.id),
                    "name": c.name,
                    "ucid": c.ucid,
                    "email": c.email,
                    "is_active": c.is_active,
                    "subscription_type": c.subscription_type.value if c.subscription_type else None,
                }
                for c in companies
            ]
            console.print_json(data=output)
        else:
            table = Table(title="Companies")
            table.add_column("UCID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Email")
            table.add_column("Status")
            table.add_column("Subscription")

            for company in companies:
                status_str = "✓ Active" if company.is_active else "✗ Inactive"
                status_color = "green" if company.is_active else "red"
                table.add_row(
                    company.ucid,
                    company.name,
                    company.email or "-",
                    f"[{status_color}]{status_str}[/{status_color}]",
                    company.subscription_type.value if company.subscription_type else "-",
                )

            console.print(table)
            console.print(f"\n[bold]Total:[/bold] {len(companies)} companies")

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}", style="bold red")
        sys.exit(1)
    finally:
        db.close()


# @app.command("create")
def create_company(
    name: str = typer.Option(..., help="Company name"),
    email: Optional[str] = typer.Option(None, help="Company email"),
    tax_id: Optional[str] = typer.Option(None, help="Tax ID"),
    pay_now: bool = typer.Option(False, "--pay", help="Enforce payment (do not skip)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """
    Create a new company.

    When --skip-payment is used (default), creates company with NATIVE subscription
    (bypasses payment workflow). This is typically for superuser manual creation.
    """
    db = SessionLocal()
    try:
        if pay_now:
            console.print("[yellow]Payment enforcement enabled[/yellow]")
        
        # Pass skip_payment = not pay_now
        company = CompanyService.create_company(
            db=db,
            name=name,
            email=email,
            tax_id=tax_id,
            skip_payment=not pay_now,
        )

        if json_output:
            output = {
                "id": str(company.id),
                "name": company.name,
                "ucid": company.ucid,
                "email": company.email,
                "tax_id": company.tax_id,
                "is_active": company.is_active,
                "subscription_type": company.subscription_type.value,
            }
            console.print_json(data=output)
        else:
            console.print(f"[green]✓[/green] Company created successfully")
            console.print(f"[bold]Name:[/bold] {company.name}")
            console.print(f"[bold]UCID:[/bold] {company.ucid}")
            console.print(f"[bold]ID:[/bold] {company.id}")
            console.print(f"[bold]Subscription:[/bold] {company.subscription_type.value}")

        sys.exit(0)

    except Exception as e:
        console.print(f"[red]Error creating company:[/red] {str(e)}", style="bold red")
        sys.exit(1)
    finally:
        db.close()


@app.command("info")
def company_info(
    company_id: str = typer.Argument(..., help="Company ID or UCID"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Get detailed information about a company."""
    db = SessionLocal()
    try:
        # Try as UCID first
        company = CompanyService.get_company_by_ucid(db, company_id)

        # If not found, try as UUID
        if not company:
            try:
                company = CompanyService.get_company_by_id(db, UUID(company_id))
            except ValueError:
                pass

        if not company:
            console.print(f"[red]Company not found:[/red] {company_id}", style="bold red")
            sys.exit(1)

        if json_output:
            output = {
                "id": str(company.id),
                "name": company.name,
                "ucid": company.ucid,
                "email": company.email,
                "phone": company.phone,
                "website": company.website,
                "address_line1": company.address_line1,
                "address_line2": company.address_line2,
                "city": company.city,
                "state": company.state,
                "postal_code": company.postal_code,
                "country": company.country,
                "tax_id": company.tax_id,
                "industry": company.industry,
                "description": company.description,
                "is_active": company.is_active,
                "subscription_type": company.subscription_type.value if company.subscription_type else None,
            }
            console.print_json(data=output)
        else:
            console.print(f"\n[bold cyan]Company Information[/bold cyan]")
            console.print(f"[bold]Name:[/bold] {company.name}")
            console.print(f"[bold]UCID:[/bold] {company.ucid}")
            console.print(f"[bold]ID:[/bold] {company.id}")
            console.print(f"[bold]Status:[/bold] {'Active' if company.is_active else 'Inactive'}")
            console.print(f"[bold]Subscription:[/bold] {company.subscription_type.value if company.subscription_type else '-'}")

            if company.email or company.phone or company.website:
                console.print(f"\n[bold cyan]Contact Information[/bold cyan]")
                if company.email:
                    console.print(f"[bold]Email:[/bold] {company.email}")
                if company.phone:
                    console.print(f"[bold]Phone:[/bold] {company.phone}")
                if company.website:
                    console.print(f"[bold]Website:[/bold] {company.website}")

            if any([company.address_line1, company.city, company.state, company.postal_code, company.country]):
                console.print(f"\n[bold cyan]Address[/bold cyan]")
                if company.address_line1:
                    console.print(f"{company.address_line1}")
                if company.address_line2:
                    console.print(f"{company.address_line2}")
                if company.city or company.state or company.postal_code:
                    parts = [p for p in [company.city, company.state, company.postal_code] if p]
                    console.print(", ".join(parts))
                if company.country:
                    console.print(f"{company.country}")

            if company.tax_id or company.industry:
                console.print(f"\n[bold cyan]Additional Information[/bold cyan]")
                if company.tax_id:
                    console.print(f"[bold]Tax ID:[/bold] {company.tax_id}")
                if company.industry:
                    console.print(f"[bold]Industry:[/bold] {company.industry}")

        sys.exit(0)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}", style="bold red")
        sys.exit(1)
    finally:
        db.close()


@app.command("delete")
def delete_company(
    company_id: str = typer.Argument(..., help="Company ID or UCID"),
    confirm: str = typer.Option(..., help="Company name for confirmation"),
):
    """Inactivate a company (soft delete)."""
    db = SessionLocal()
    try:
        # Try as UCID first
        company = CompanyService.get_company_by_ucid(db, company_id)

        if not company:
            try:
                company = CompanyService.get_company_by_id(db, UUID(company_id))
                if company:
                    company_id = company.ucid
            except ValueError:
                pass

        if not company:
            console.print(f"[red]Company not found:[/red] {company_id}", style="bold red")
            sys.exit(1)

        # Inactivate using existing service
        CompanyService.inactivate_company(db, company_id, confirm)

        console.print(f"[green]✓[/green] Company '{company.name}' inactivated successfully")
        sys.exit(0)

    except ValueError as e:
        console.print(f"[red]Error:[/red] {str(e)}", style="bold red")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {str(e)}", style="bold red")
        sys.exit(1)
    finally:
        db.close()
