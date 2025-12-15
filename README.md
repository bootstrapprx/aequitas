# Aequitas - Integrated Accounting System

**Aequitas** is a complete accounting system featuring intelligent chart of accounts management, financial reporting, and integrated bookkeeping. Built with a modern React frontend and powerful FastAPI backend, Aequitas provides a seamless experience for managing your company's financial operations.

## ✨ Features

### Core Accounting
- **Dashboard:** Overview of companies, users, and recent activity
- **Registration Module:** Centralized management of companies, users, and charts of accounts
- **GroupCompany (Umbrella View):** Manage multiple companies under a single group with shared mappings
- **Accountancy Module:** Complete accounting cycle with journal entries, daily ledger, trial balance, and fiscal periods
- **Reports Module:** Financial statements (Balance Sheet, Income Statement, Cash Flow) with export capabilities
- **Administration:** System settings, integrations, and audit logs

### Digital Athenaeum Theme
- **Classical Interface:** Marble textures, gold accents, and ancient manuscript aesthetics
- **Micro-interactions:** Animated quills, unfurling scrolls, and wax seal badges
- **Themed Pages:** "Scribe's Chamber" (Journal), "Hall of Balance" (Trial Balance), "Auditor's Tower" (Statements)
- **Immersive Experience:** Combines modern functionality with classical architecture metaphors

### Chart of Accounts - Intelligent Management
- **Master Chart Management:** Create and maintain standardized chart of accounts
- **AI-Powered Mapping:** Automatic account classification and mapping using AI
- **QuickBooks Integration:** OAuth2-based sync with QuickBooks Online
- **Template System:** Reusable chart of accounts templates
- **Import/Export:** Excel-based data exchange
- **Mapping Propagation:** Copy account mappings across companies in a group

### Technical Features
- **Intuitive Frontend:** Responsive UI built with React, Vite, Tailwind CSS, and shadcn/ui
- **Powerful Backend:** Robust REST API built with FastAPI and Python
- **Database Integration:** PostgreSQL with SQLAlchemy for reliable data storage
- **AI-Powered Organization:**
    - **Local AI:** Uses Ollama for local, private accounting classification
    - **Cloud AI:** Supports Cloudflare Workers AI for edge-based inference
- **Dynamic Settings:** Manage API keys and integrations directly from the UI
- **Containerized Environment:** Full Docker and Docker Compose setup for easy development and deployment
- **UCID Generation:** Automatic generation of Unique Company IDs using standardized normalization and hashing

## 📂 Project Structure

The project is organized into two main directories: `frontend` and `backend`.

```
/
├── backend/         # FastAPI application
│   ├── app/
│   │   ├── api/v1/          # API routes
│   │   ├── db/              # Database models and session
│   │   ├── services/        # Business logic
│   │   └── main.py          # FastAPI app entry point
│   ├── Dockerfile
│   └── docker-compose.yml
├── frontend/        # React application
│   ├── src/
│   │   ├── pages/           # Page components
│   │   │   ├── dashboard/   # Main dashboard
│   │   │   ├── registration/ # Companies, users, CoA
│   │   │   ├── groups/      # Company groups (umbrella view)
│   │   │   ├── chartforge/  # Chart of Accounts module
│   │   │   ├── accountancy/ # Accounting operations
│   │   │   ├── reports/     # Financial reports
│   │   │   └── admin/       # Administration
│   │   ├── components/      # Reusable components
│   │   └── App.tsx          # Main app component
│   ├── package.json
│   └── vite.config.ts
├── docs/            # Documentation and guides
├── assets/          # Excel workbooks and resources
└── README.md        # This file
```

## 🖥️ Command-Line Interface (CLI)

Aequitas includes a powerful CLI for administrative, operational, and diagnostic tasks:

```bash
# Install CLI
cd backend && pip install -e .

# Quick examples
aequitas companies list                    # List all companies
aequitas groups create "My Group"          # Create a company group
aequitas mappings propagate -s SRC -g GRP  # Propagate account mappings
aequitas db upgrade                        # Run database migrations
aequitas diag health                       # Check system health
```

**CLI Features:**
- Full CRUD operations for companies, groups, users, and mappings
- Database migration management (Alembic integration)
- Logs viewing and export
- System diagnostics and health checks
- JSON output mode for scripting
- Rich, colorized terminal output

See [docs/cli.md](docs/cli.md) for complete CLI documentation.

### ⚡ Quick Access with 'aq'

For Docker users, a convenience wrapper script is available at the project root:

```bash
./aq companies list
./aq diag health
```

This is equivalent to running `docker compose exec backend python -m cli.main ...`.

## 🚀 Getting Started

### Prerequisites

- **Docker** and **Docker Compose** installed on your machine
- **Node.js** (v18+) and **pnpm** for local frontend development
- **Python** (3.11+) for local backend development

### Quick Start with Docker (Recommended)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/bootstrapprx/Aequitas.git
   cd Aequitas
   ```

2. **Set up environment variables:**
   ```bash
   # Backend
   cp backend/.env.example backend/.env
   # Edit backend/.env with your configuration
   
   # Frontend
   cp frontend/.env.example frontend/.env
   # Edit frontend/.env with your configuration
   ```

3. **Start the application:**
   ```bash
   make dev
   ```

4. **Access the application:**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Ollama: http://localhost:11435
   - Postgres: localhost:5432

### Makefile Commands

#### Development Commands
```bash
make dev          # Start development environment
make stop         # Stop all services
make logs         # View container logs
```

#### Reset & Rebuild Commands
```bash
make reset        # Complete reset (stops, removes volumes, rebuilds)
make rebuild      # Force rebuild containers without cache
make reset-db     # Reset only the database
```

#### Dependency Management

**For Docker-based development (recommended):**
```bash
make rebuild      # Rebuilds containers with fresh dependencies
```

**For local IDE support or local development:**
```bash
make install-deps         # Install all dependencies locally (frontend + backend)
make install-frontend     # Install only frontend dependencies locally
make install-backend      # Install only backend dependencies locally

make clean-deps           # Clean all local dependency caches
make reinstall-frontend   # Clean and reinstall frontend dependencies locally
make reinstall-backend    # Clean and reinstall backend dependencies locally
make reinstall-deps       # Clean and reinstall all dependencies locally
```

**Important:** When using Docker (recommended), dependency changes are automatically handled by `make rebuild`. The local install commands are only needed to:
- Fix IDE TypeScript/ESLint errors
- Run the app outside Docker for development

**Typical Docker workflow when dependencies change:**
1. Run `make rebuild` - That's it! Dependencies are installed inside containers.

### Local Development (Without Docker)

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

## 📚 Documentation

- **[Master Chart Guide](MASTER_CHART.md)** - Complete guide to the US-GAAP master chart of accounts
- **[Technical Report](docs/technical_report.md)** - Detailed methodology and implementation
- **[Chart of Accounts Guide](docs/ChartOfAccounts_Guide.pdf)** - Comprehensive accounting guide
- **[Enriched Chart README](backend/app/data/ENRICHED_CHART_README.md)** - Enhanced chart features
- **[Transformation Plan](AEQUITAS_TRANSFORMATION_PLAN.md)** - Aequitas architecture and roadmap

## 🎯 Modules

### Dashboard
Main landing page with company overview, user stats, and recent activity feed.

### Registration
- **Companies:** Manage multiple companies with separate charts of accounts
- **Users:** User management and access control
- **Chart of Accounts:** Simple CoA registration and management

### Chart of Accounts (Intelligent Module)
- **Master Chart:** Standardized US-GAAP chart of accounts (345 accounts)
- **Mapping:** Automatic and manual account mapping
- **Import/Export:** Excel-based data exchange
- **AI Organizer (Dexter):** AI-powered account classification

### Accountancy ✅
- **Scribe's Chamber (Journal Entries):** Create, post, void, and delete journal entries
- **Ledger of Days (Daily Ledger):** Daily journal entry management with search and filters
- **Hall of Balance (Trial Balance):** Generate trial balance by period or date
- **Chronicle of Time (Fiscal Periods):** Manage accounting periods with open/closed/locked states
- **Complete Accounting Cycle:** Full double-entry bookkeeping with GAAP compliance

### Reports ✅
- **Auditor's Tower (Financial Statements):** Balance Sheet, Income Statement, Cash Flow
- **Ancient Scroll Presentation:** Reports displayed with unfurling scroll animations
- **Export Center:** Export statements to CSV format
- **Period-Based Reporting:** Generate reports by fiscal period or date range

### Administration
- **System Settings:** Application configuration
- **Integrations:** QuickBooks and other integrations
- **Audit Log:** System activity tracking

### Company Groups (Umbrella View)
- **Group Management:** Create and manage groups of related companies
- **Company Association:** Add/remove companies from groups
- **Mapping Propagation:** Copy account mappings from one company to all others in the group
- **SU Manual Company Creation:** Superusers can create companies bypassing payment workflow
- **Centralized Management:** Manage multiple companies under a single umbrella

**Use Case:** Bob owns 5 restaurant locations. Instead of manually mapping accounts for each location, Bob can:
1. Create a "Bob's Restaurant Group"
2. Add all 5 locations to the group
3. Set up mappings once for the first location
4. Propagate mappings to all other locations automatically
5. When adding a new location, use SU-create to bypass payment and auto-add to group

See [docs/groups.md](docs/groups.md) for detailed documentation.

## 🔐 Authentication

Aequitas uses JWT-based authentication with role-based access control:

- **Superuser:** Full system access
- **Admin:** Company-level administration
- **User:** Standard user access

Default superuser credentials (change immediately):
- Email: admin@aequitas.local
- Password: admin123

## 🤖 AI Features

### Dexter - AI Accounting Assistant
Dexter is an AI-powered assistant that helps with:
- Account classification and mapping
- Natural language queries about your chart of accounts
- Intelligent suggestions for account organization

### AI Organizer
Automatic classification of uploaded accounts using:
- **Ollama** (local, private)
- **Cloudflare Workers AI** (edge-based)

## 🔗 Integrations

### QuickBooks Online
- OAuth2-based authentication
- Automatic account synchronization
- Bidirectional data sync
- Token refresh handling

### Future Integrations
- Xero
- Sage
- NetSuite
- Custom API integrations

## 📊 Master Chart of Accounts

Aequitas includes a comprehensive US-GAAP master chart with:
- **345 accounts** (7 headers + 338 details)
- **Complete IFRS/US-GAAP compliance**
- **AI-ready tags** for automatic categorization
- **Vendor mappings** for 59 expense accounts
- **Regulatory references** (IAS, IFRS, ASC)
- **Professional descriptions** for all accounts

See [MASTER_CHART.md](MASTER_CHART.md) for complete details.

## 🛠️ Technology Stack

### Frontend
- **React 18** with TypeScript
- **Vite** for fast development
- **Tailwind CSS** for styling
- **shadcn/ui** component library
- **Tanstack Query** for data fetching
- **React Router** for navigation
- **Framer Motion** for animations

### Backend
- **FastAPI** (Python 3.11+)
- **PostgreSQL** database
- **SQLAlchemy** ORM
- **Alembic** for migrations
- **Pydantic** for validation
- **JWT** authentication
- **Ollama** for local AI
- **Cloudflare Workers AI** for cloud AI

### DevOps
- **Docker** & **Docker Compose**
- **GitHub Actions** for CI/CD
- **PostgreSQL** containerized database

## 🏛️ Digital Athenaeum Theme

Aequitas features a unique "Digital Athenaeum of Finance" interface that combines classical architecture metaphors with modern accounting functionality.

### Theme Components

The Athenaeum component library (`frontend/src/components/athenaeum/`) includes:

- **PageHeader:** Classical page headers with embossed gold text and animated icons
- **AtheneumCard:** Marble-textured cards with hover effects and glow
- **WaxSealBadge:** Animated wax seal status indicators (approved, rejected, pending, locked, unlocked)
- **ScrollUnfurl:** Ancient scroll unfurling animations for financial reports
- **QuillIcon:** Animated quill icon for writing operations

### Visual Design

- **Color Palette:** Emerald primary, gold/bronze accents, marble textures
- **Typography:** Playfair Display (headings) + DM Sans (body)
- **Animations:** Quill writing, scroll unfurling, wax seal stamping, ink fading
- **Utilities:** Parchment paper, embossed gold text, ornate borders, manuscript lines

### Themed Page Names

Core accounting pages feature classical, immersive names:

| Page | Classical Name | Theme |
|------|---------------|-------|
| Journal Entries | Scribe's Chamber | Ancient scribes recording in ledgers |
| Daily Ledger | Ledger of Days | Chronicle of daily financial records |
| Trial Balance | Hall of Balance | Weighing debits and credits on scales |
| Fiscal Periods | Chronicle of Time | Guardians of accounting cycles |
| Financial Statements | Auditor's Tower | Ancient scrolls of financial wisdom |

### Implementation

The theme is built with:
- **Framer Motion** for smooth animations
- **Custom CSS utilities** in Tailwind
- **Reusable components** following shadcn/ui patterns
- **Performance-optimized** animations with optional disable

For complete documentation on using the Athenaeum theme, see [CLAUDE.md - Athenaeum Theme section](CLAUDE.md#athenaeum-theme--recent-transformations).

## 📈 Roadmap

### Phase 1-3: Foundation & Core Features ✅ (Completed)
- [x] Dashboard and navigation
- [x] Company management
- [x] Chart of Accounts module with AI-powered mapping
- [x] User authentication and management
- [x] Master chart normalization and validation
- [x] Mapping engine consolidation
- [x] Daily ledger / journal entries
- [x] Trial balance generation
- [x] Fiscal period management
- [x] Financial statements (Balance Sheet, Income Statement, Cash Flow)
- [x] Export capabilities

### Phase 4-5: Transformation & Theme ✅ (Completed)
- [x] Accounting engine integration
- [x] Complete accounting cycle implementation
- [x] Fiscal period CRUD operations
- [x] Digital Athenaeum theme
- [x] Athenaeum component library
- [x] Classical page designs
- [x] Micro-interactions and animations
- [x] Ancient manuscript aesthetics

### Phase 6: Enhancement & Scale (Current)
- [ ] Custom report builder
- [ ] Advanced analytics dashboard
- [ ] Budget management
- [ ] Forecasting tools
- [ ] Multi-currency support
- [ ] Additional integrations (Xero, Sage)

### Phase 7: Advanced Features (Future)
- [ ] Mobile application
- [ ] Advanced AI features
- [ ] Automated reconciliation
- [ ] Predictive analytics
- [ ] Multi-entity consolidation

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is proprietary software. All rights reserved.

## 📧 Support

For questions, issues, or feature requests:
- Open an issue on GitHub
- Contact: support@aequitas.local

## 🙏 Acknowledgments

- **shadcn/ui:** Beautiful and accessible component library
- **FastAPI:** Modern, fast web framework for building APIs
- **Ollama:** Local AI inference engine

---

**Aequitas** - *Fairness and Justice in Accounting* ⚖️

Built with ❤️ for accountants, by developers who care about financial accuracy.
