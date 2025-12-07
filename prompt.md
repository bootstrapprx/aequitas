You are now tasked with creating a complete, modular, production-ready CLI for the Aequitas system.
This CLI must run side-by-side with the existing backend and serve as a full administrative, operational, diagnostic and development companion to the web version.

Work inside the existing aequitas repository.

🎯 OBJECTIVE

Implement a full Aequitas CLI using Typer (preferred) to provide:

1. Administrative operations

Create/list/delete companies

Superuser-only “manual creation” (bypass payment)

Manage groups (GroupCompany)

Mapping propagation

User controls

2. Developer/Operator utilities

Database migrations (upgrade/downgrade)

DB inspection

Seed commands

Log viewer / internal logs dumper

Health check commands

Internal service runners (mapping engine, maintenance tasks)

3. Observability

Session logs

System activity logs

Error dumps

JSON/pretty output switches

4. Modularity and easy extension

Organize all commands under:

backend/cli/
    __main__.py
    main.py
    commands/
        companies.py
        groups.py
        mappings.py
        users.py
        logs.py
        db.py
        diagnostics.py


Make the CLI available via:

aequitas <command> [options]


using an entrypoint (pyproject or setup scripts).

📦 HIGH-LEVEL REQUIREMENTS
CLI must:

Use Typer

Use the actual backend database & services (no mocks)

Reuse existing service functions wherever possible

Support JSON or human-readable output (--json flag on all major commands)

Have complete, consistent auto-generated help documentation

Have excellent error reporting

Never break existing backend code

All commands must:

Open DB sessions correctly

Validate permissions when needed (e.g., SU actions)

Produce graceful error messages

Return exit codes correctly (0 success, 1 failure)

📁 DETAILED STRUCTURE TO IMPLEMENT
1. CLI Root Application

File: backend/cli/main.py

Create Typer app named “Aequitas CLI”

Load sub-commands from backend/cli/commands/*

Add global options:

--debug → enable verbose logging

--json → return only JSON dict output

Entrypoint runner in backend/cli/__main__.py:

from .main import app
app()


Add to pyproject.toml:

[project.scripts]
aequitas = "backend.cli.__main__:app"

2. Companies Commands

File: backend/cli/commands/companies.py

Implement:

aequitas companies list

List all companies with essential metadata

Support --json

aequitas companies create

Arguments:

--name

--tax-id

--group-id

--skip-payment (default=True)

SU permission check

aequitas companies delete <company_id>

Soft delete or mark inactive depending current backend rules

aequitas companies info <company_id>

Full structured output

Internally call existing service layer:

company_service.create_company

company_service.list_companies

validation against User.is_superuser

3. GroupCompany Commands

File: backend/cli/commands/groups.py

Implement:

aequitas groups list
aequitas groups create <name> [--description TEXT]
aequitas groups add-company <group_id> <company_id>
aequitas groups remove-company <group_id> <company_id>
aequitas groups info <group_id>

Reuse the backend GroupCompany implementation.

4. Mappings Commands

File: backend/cli/commands/mappings.py

Implement:

aequitas mappings propagate --source <company_id> --targets <ids...> [--force]

Call backend mapping propagation service.

aequitas mappings list <company_id>

List mapping rows.

5. Users Commands

File: backend/cli/commands/users.py

Implement:

aequitas users list
aequitas users create --email EMAIL --su/--no-su
aequitas users info <user_id>

Add SU-only enforcement where needed.

6. Database Commands

File: backend/cli/commands/db.py

Implement:

aequitas db upgrade

Run alembic upgrade head.

aequitas db downgrade

Downgrade one revision.

aequitas db revision --msg "message"

Generate new migration.

aequitas db inspect

Print database tables, row counts, or summary.

aequitas db seed

Call any seed scripts (you create a simple driver).

7. Logs Commands

File: backend/cli/commands/logs.py

Implement:

aequitas logs tail

Follow backend logs (via subprocess to journalctl or log file)

aequitas logs session

Dump internal session/activity logs

aequitas logs dump

Export logs to file

8. Diagnostics Commands

File: backend/cli/commands/diagnostics.py

Implement:

aequitas diag health

Ping DB, run small query.

aequitas diag version

Return app version, environment, Python version.

aequitas diag env

Display environment variables (safe subset).

🧪 TESTS

Create backend/tests/test_cli.py covering:

CLI entrypoint loads

Companies list

Groups create

SU create via CLI

Mapping propagation command

DB upgrade/downgrade

JSON output flag

Exit codes

Use CliRunner from Typer.

📘 DOCUMENTATION

Create docs/cli.md including:

Installation & usage

Command reference (auto-generated help + examples)

Architecture

Integration with backend

How to extend CLI with new commands

Add CLI section to main README.md.

📌 ACCEPTANCE CRITERIA

Claude must deliver:

New folder structure under backend/cli/

All commands implemented and wired to backend services

Fully functional Typer CLI available via aequitas executable

Commands tested with pytest

Documentation completed

Commits small and atomic, branch name: feature/cli

Final output message confirming success

📝 REQUIRED FINAL OUTPUT FROM CLAUDE

Claude should output at completion:

“Aequitas CLI created successfully. Branch feature/cli with all modules, commands, entrypoint, tests, and documentation is ready. You may now run aequitas --help.”