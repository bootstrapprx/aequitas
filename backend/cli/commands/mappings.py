"""Account mappings management commands."""

import typer
import sys
from rich.console import Console
from rich.table import Table
from typing import Optional, List
from uuid import UUID

from app.db.session import SessionLocal
from app.services.group_service import GroupService
from app.db.models.account_mapping import AccountMapping
from app.db.models.company_account import CompanyAccount

console = Console()
app = typer.Typer()


@app.command("list")
def list_mappings(
    company_id: str = typer.Argument(..., help="Company ID or UCID"),
    status: Optional[str] = typer.Option(None, help="Filter by status (suggested, confirmed, rejected)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """List account mappings for a company."""
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

        # Get mappings
        query = db.query(AccountMapping).join(
            CompanyAccount,
            AccountMapping.company_account_id == CompanyAccount.id
        ).filter(
            CompanyAccount.company_id == company.id
        )

        if status:
            query = query.filter(AccountMapping.status == status)

        mappings = query.all()

        if json_output:
            output = [
                {
                    "id": str(m.id),
                    "company_account_id": str(m.company_account_id),
                    "master_code": m.master_code,
                    "confidence": m.confidence,
                    "status": m.status,
                    "propagated_from": str(m.propagated_from) if m.propagated_from else None,
                    "notes": m.notes,
                }
                for m in mappings
            ]
            console.print_json(data=output)
        else:
            table = Table(title=f"Account Mappings for {company.name}")
            table.add_column("Account ID", style="dim")
            table.add_column("Master Code", style="cyan")
            table.add_column("Confidence", style="green")
            table.add_column("Status")
            table.add_column("Propagated", style="yellow")

            for mapping in mappings:
                table.add_row(
                    str(mapping.company_account_id)[:8] + "...",
                    mapping.master_code or "-",
                    f"{mapping.confidence:.2f}",
                    mapping.status,
                    "Yes" if mapping.propagated_from else "No",
                )

            console.print(table)
            console.print(f"\n[bold]Total:[/bold] {len(mappings)} mappings")

        sys.exit(0)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}", style="bold red")
        sys.exit(1)
    finally:
        db.close()


@app.command("propagate")
def propagate_mappings(
    source: str = typer.Option(..., "-s", help="Source company ID or UCID"),
    group_id: str = typer.Option(..., "-g", help="Group ID"),
    targets: Optional[List[str]] = typer.Option(None, "-t", help="Target company IDs (optional, all if not specified)"),
    force: bool = typer.Option(False, "-f", help="Force overwrite existing mappings"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """
    Propagate account mappings from source company to others in a group.

    Example:
        aequitas mappings propagate --source COMP1 --group GROUP_ID --force
    """
    db = SessionLocal()
    try:
        # Resolve source company ID
        from app.services.company_service import CompanyService
        source_company = CompanyService.get_company_by_ucid(db, source)
        if not source_company:
            try:
                source_company = CompanyService.get_company_by_id(db, UUID(source))
            except ValueError:
                pass

        if not source_company:
            console.print(f"[red]Source company not found:[/red] {source}", style="bold red")
            sys.exit(1)

        # Resolve target company ID if specified
        target_company_id = None
        if targets and len(targets) > 0:
            target = targets[0]  # For now, support single target
            target_company = CompanyService.get_company_by_ucid(db, target)
            if not target_company:
                try:
                    target_company = CompanyService.get_company_by_id(db, UUID(target))
                except ValueError:
                    pass

            if target_company:
                target_company_id = target_company.id

        # Propagate
        result = GroupService.propagate_mappings(
            db=db,
            group_id=UUID(group_id),
            source_company_id=source_company.id,
            target_company_id=target_company_id,
            force=force,
        )

        if json_output:
            console.print_json(data=result)
        else:
            console.print(f"[green]✓[/green] Mapping propagation completed")
            console.print(f"[bold]Source company:[/bold] {source_company.name}")
            console.print(f"[bold]Target companies:[/bold] {result['target_companies']}")
            console.print(f"[bold]Source mappings:[/bold] {result['source_mappings']}")
            console.print(f"[bold green]Created:[/bold green] {result['created']}")
            console.print(f"[bold yellow]Updated:[/bold yellow] {result['updated']}")
            console.print(f"[bold]Skipped:[/bold] {result['skipped']}")

        sys.exit(0)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}", style="bold red")
        sys.exit(1)
    finally:
        db.close()
