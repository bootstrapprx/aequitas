# Aequitas CLI Documentation

## Overview

The Aequitas CLI is a command-line interface tool for administrative, operational, diagnostic, and development tasks in the Aequitas accounting system. Built with Typer and Rich, it provides a comprehensive set of commands that interact directly with the backend database and services.

## Installation

### From Source

```bash
cd backend
pip install -e .
```

This installs the `aequitas` command globally.

### With Docker

If running in Docker, you can execute CLI commands inside the backend container:

```bash
docker compose exec backend python -m cli.main --help
```

## Quick Start

```bash
# Get help
aequitas --help

# List all companies
aequitas companies list

# Create a new company (SU bypasses payment)
aequitas companies create --name "My Company" --email "contact@mycompany.com"

# Check system health
aequitas diag health

# View database tables
aequitas db inspect
```

## Global Options

All commands support these global flags:

- `--debug` - Enable debug mode with verbose output
- `--json` - Output results as JSON (useful for scripting)

Example:
```bash
aequitas --json companies list
aequitas --debug diag health
```

---

## Command Reference

### Companies Management

#### `aequitas companies list`

List all companies in the system.

**Options:**
- `--status` - Filter by status: `active`, `inactive`, or `all` (default: `active`)
- `--json` - Output as JSON

**Examples:**
```bash
# List active companies
aequitas companies list

# List inactive companies
aequitas companies list --status inactive

# List all companies as JSON
aequitas companies list --status all --json
```

---

#### `aequitas companies create`

Create a new company.

**Options:**
- `--name` (required) - Company name
- `--email` - Company email
- `--tax-id` - Tax ID / EIN
- `--skip-payment / --no-skip-payment` - Skip payment workflow (default: `True`, creates NATIVE subscription)
- `--json` - Output as JSON

**Examples:**
```bash
# Create company with NATIVE subscription (bypasses payment)
aequitas companies create --name "Acme Corp" --email "contact@acme.com"

# Create company requiring Stripe payment
aequitas companies create --name "Beta Inc" --no-skip-payment

# Create with tax ID
aequitas companies create --name "Gamma LLC" --tax-id "12-3456789" --json
```

---

#### `aequitas companies info <company_id>`

Get detailed information about a company.

**Arguments:**
- `company_id` - Company ID (UUID) or UCID

**Options:**
- `--json` - Output as JSON

**Examples:**
```bash
# Get info by UCID
aequitas companies info ACME

# Get info by UUID
aequitas companies info 123e4567-e89b-12d3-a456-426614174000

# Get info as JSON
aequitas companies info ACME --json
```

---

#### `aequitas companies delete <company_id>`

Inactivate a company (soft delete).

**Arguments:**
- `company_id` - Company ID or UCID

**Options:**
- `--confirm` (required) - Company name for confirmation

**Examples:**
```bash
aequitas companies delete ACME --confirm "Acme Corp"
```

---

### Groups Management

#### `aequitas groups list`

List all company groups.

**Options:**
- `--json` - Output as JSON

**Examples:**
```bash
aequitas groups list
aequitas groups list --json
```

---

#### `aequitas groups create <name>`

Create a new company group.

**Arguments:**
- `name` - Group name

**Options:**
- `--description, -d` - Group description
- `--owner` - Owner user ID (defaults to first superuser)
- `--json` - Output as JSON

**Examples:**
```bash
# Create group with default owner
aequitas groups create "Bob's Restaurants"

# Create with description
aequitas groups create "Tech Startups" --description "Portfolio of tech companies"

# Create with specific owner
aequitas groups create "Finance Group" --owner USER_UUID --json
```

---

#### `aequitas groups info <group_id>`

Get detailed information about a group including member companies.

**Arguments:**
- `group_id` - Group ID (UUID)

**Options:**
- `--json` - Output as JSON

**Examples:**
```bash
aequitas groups info GROUP_UUID
aequitas groups info GROUP_UUID --json
```

---

#### `aequitas groups add-company <group_id> <company_id>`

Add a company to a group.

**Arguments:**
- `group_id` - Group ID
- `company_id` - Company ID or UCID

**Examples:**
```bash
aequitas groups add-company GROUP_UUID ACME
aequitas groups add-company GROUP_UUID 123e4567-e89b-12d3-a456-426614174000
```

---

#### `aequitas groups remove-company <group_id> <company_id>`

Remove a company from a group.

**Arguments:**
- `group_id` - Group ID
- `company_id` - Company ID or UCID

**Examples:**
```bash
aequitas groups remove-company GROUP_UUID ACME
```

---

### Mappings Management

#### `aequitas mappings list <company_id>`

List account mappings for a company.

**Arguments:**
- `company_id` - Company ID or UCID

**Options:**
- `--status` - Filter by status (`suggested`, `confirmed`, `rejected`)
- `--json` - Output as JSON

**Examples:**
```bash
# List all mappings
aequitas mappings list ACME

# List only confirmed mappings
aequitas mappings list ACME --status confirmed

# List as JSON
aequitas mappings list ACME --json
```

---

#### `aequitas mappings propagate`

Propagate account mappings from source company to others in a group.

**Options:**
- `--source, -s` (required) - Source company ID or UCID
- `--group, -g` (required) - Group ID
- `--target, -t` - Target company ID (optional, propagates to all if not specified)
- `--force, -f` - Force overwrite existing mappings
- `--json` - Output as JSON

**Examples:**
```bash
# Propagate to all companies in group
aequitas mappings propagate --source ACME --group GROUP_UUID

# Propagate to specific company
aequitas mappings propagate --source ACME --group GROUP_UUID --target BETA

# Force overwrite existing mappings
aequitas mappings propagate --source ACME --group GROUP_UUID --force

# Get JSON output
aequitas mappings propagate -s ACME -g GROUP_UUID --json
```

---

### Users Management

#### `aequitas users list`

List all users.

**Options:**
- `--json` - Output as JSON

**Examples:**
```bash
aequitas users list
aequitas users list --json
```

---

#### `aequitas users create`

Create a new user.

**Options:**
- `--email, -e` (required) - User email
- `--password, -p` (required) - User password
- `--su / --no-su` - Make user a superuser (default: `False`)
- `--role, -r` - User role: `USER`, `ACCOUNTANT`, `ADMIN`, `SU` (default: `USER`)
- `--json` - Output as JSON

**Examples:**
```bash
# Create regular user
aequitas users create --email "user@example.com" --password "securepass"

# Create superuser
aequitas users create --email "admin@example.com" --password "adminpass" --su

# Create with specific role
aequitas users create -e "accountant@example.com" -p "pass123" --role ACCOUNTANT --json
```

---

#### `aequitas users info <user_id>`

Get detailed information about a user.

**Arguments:**
- `user_id` - User ID (UUID) or email

**Options:**
- `--json` - Output as JSON

**Examples:**
```bash
# Get info by email
aequitas users info user@example.com

# Get info by UUID
aequitas users info USER_UUID

# Get as JSON
aequitas users info user@example.com --json
```

---

### Database Operations

#### `aequitas db upgrade`

Run database migrations (alembic upgrade).

**Options:**
- `--revision, -r` - Revision to upgrade to (default: `head`)

**Examples:**
```bash
# Upgrade to latest
aequitas db upgrade

# Upgrade to specific revision
aequitas db upgrade --revision abc123
```

---

#### `aequitas db downgrade`

Downgrade database migrations (alembic downgrade).

**Options:**
- `--steps, -n` - Number of revisions to downgrade (default: `1`)

**Examples:**
```bash
# Downgrade one revision
aequitas db downgrade

# Downgrade 3 revisions
aequitas db downgrade --steps 3

# Downgrade to base
aequitas db downgrade --steps 0
```

---

#### `aequitas db revision`

Create a new database migration.

**Options:**
- `--msg, -m` (required) - Revision message
- `--autogenerate / --no-autogenerate` - Auto-generate migration from models (default: `True`)

**Examples:**
```bash
# Create migration with autogenerate
aequitas db revision --msg "add user preferences table"

# Create empty migration
aequitas db revision --msg "custom migration" --no-autogenerate
```

---

#### `aequitas db inspect`

Inspect database tables and row counts.

**Options:**
- `--json` - Output as JSON

**Examples:**
```bash
aequitas db inspect
aequitas db inspect --json
```

---

#### `aequitas db seed`

Seed database with initial data.

**Options:**
- `--master-chart` - Seed master chart

**Examples:**
```bash
# Seed master chart
aequitas db seed --master-chart
```

---

### Logs Management

#### `aequitas logs tail`

Tail backend logs.

**Options:**
- `--lines, -n` - Number of lines to show (default: `50`)
- `--follow, -f` - Follow log output (live tail)

**Examples:**
```bash
# Show last 50 lines
aequitas logs tail

# Show last 100 lines
aequitas logs tail --lines 100

# Follow logs in real-time
aequitas logs tail --follow
```

**Note:** For Docker deployments, use `docker compose logs backend` instead.

---

#### `aequitas logs session`

Dump internal session/activity logs from database.

**Options:**
- `--limit, -n` - Number of session logs to show (default: `100`)
- `--json` - Output as JSON

**Examples:**
```bash
aequitas logs session
aequitas logs session --limit 50 --json
```

---

#### `aequitas logs dump`

Export logs to a file.

**Options:**
- `--output, -o` - Output file path (default: `logs_dump.txt`)

**Examples:**
```bash
aequitas logs dump
aequitas logs dump --output my_logs.txt
```

---

### Diagnostics

#### `aequitas diag health`

Run health checks on database and system.

**Options:**
- `--json` - Output as JSON

**Examples:**
```bash
aequitas diag health
aequitas diag health --json
```

---

#### `aequitas diag version`

Display version information.

**Options:**
- `--json` - Output as JSON

**Examples:**
```bash
aequitas diag version
aequitas diag version --json
```

---

#### `aequitas diag env`

Display environment configuration (safe subset).

**Options:**
- `--show-secrets` - Show sensitive values (⚠️ dangerous!)
- `--json` - Output as JSON

**Examples:**
```bash
# Show safe environment variables
aequitas diag env

# Show all including secrets
aequitas diag env --show-secrets

# Get as JSON
aequitas diag env --json
```

---

## Architecture

### Structure

```
backend/
├── cli/
│   ├── __init__.py
│   ├── __main__.py          # Entry point
│   ├── main.py              # Main Typer app
│   └── commands/
│       ├── __init__.py
│       ├── companies.py     # Companies commands
│       ├── groups.py        # Groups commands
│       ├── mappings.py      # Mappings commands
│       ├── users.py         # Users commands
│       ├── db.py            # Database commands
│       ├── logs.py          # Logs commands
│       └── diagnostics.py   # Diagnostics commands
└── setup.py                 # CLI entry point configuration
```

### Integration with Backend

The CLI directly uses:
- **Database Session:** `app.db.session.SessionLocal()`
- **Services:** `CompanyService`, `GroupService`, etc.
- **Models:** All SQLAlchemy models
- **Config:** `app.core.config.settings`

This ensures consistency between the web API and CLI operations.

### Error Handling

All commands follow these conventions:
- **Exit code 0:** Success
- **Exit code 1:** Error
- Errors are printed in red with descriptive messages
- JSON output mode omits color formatting

---

## Extending the CLI

### Adding a New Command Module

1. **Create command file:**
   ```python
   # backend/cli/commands/mymodule.py
   import typer
   from rich.console import Console

   console = Console()
   app = typer.Typer()

   @app.command("mycommand")
   def my_command(
       arg: str = typer.Argument(..., help="Description"),
       json_output: bool = typer.Option(False, "--json"),
   ):
       """Command description."""
       try:
           # Your logic here
           console.print("[green]Success![/green]")
           sys.exit(0)
       except Exception as e:
           console.print(f"[red]Error:[/red] {str(e)}")
           sys.exit(1)
   ```

2. **Register in main.py:**
   ```python
   from cli.commands import mymodule

   app.add_typer(mymodule.app, name="mymodule", help="My module commands")
   ```

3. **Add tests:**
   ```python
   def test_mymodule_command():
       result = runner.invoke(app, ["mymodule", "mycommand", "test"])
       assert result.exit_code == 0
   ```

### Best Practices

- Always support `--json` flag for scriptability
- Use Rich console for pretty output
- Return proper exit codes (0 = success, 1 = error)
- Provide helpful error messages
- Close database sessions in `finally` blocks
- Add comprehensive help text to all commands

---

## Scripting Examples

### Batch Company Creation

```bash
#!/bin/bash
# Create multiple companies from CSV

while IFS=',' read -r name email tax_id; do
  aequitas companies create \
    --name "$name" \
    --email "$email" \
    --tax-id "$tax_id" \
    --json >> companies_created.json
done < companies.csv
```

### Health Monitoring

```bash
#!/bin/bash
# Monitor system health

aequitas diag health --json > health_check.json

if [ $? -eq 0 ]; then
  echo "System healthy"
else
  echo "System unhealthy" | mail -s "Aequitas Health Alert" admin@example.com
fi
```

### Automated Mapping Propagation

```bash
#!/bin/bash
# Propagate mappings to all groups

groups=$(aequitas groups list --json | jq -r '.[].id')

for group_id in $groups; do
  aequitas mappings propagate \
    --source SOURCE_COMPANY \
    --group "$group_id" \
    --json
done
```

---

## Troubleshooting

### CLI Not Found

If `aequitas` command is not found:

```bash
cd backend
pip install -e .
```

Or use Python module:
```bash
python -m cli.main --help
```

### Database Connection Errors

Ensure environment variables are set:

```bash
export DATABASE_URL="postgresql+psycopg2://user:password@localhost:5432/aequitas_dev"
aequitas diag health
```

### Import Errors

Make sure you're in the backend directory or have it in your Python path:

```bash
cd backend
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
aequitas --help
```

---

## Related Documentation

- [Main README](../README.md)
- [Groups Documentation](./groups.md)
- [API Documentation](http://localhost:8000/docs)
