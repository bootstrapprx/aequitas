# Meta Engine GUI

Desktop application for the Aequitas Meta Engine governance tool.

## Requirements

- Rust 1.92+
- Node.js 18+
- npm
- Tauri system dependencies (see https://tauri.app/v2/guides/prerequisites/)

## Development

### First Time Setup

```bash
# Install npm dependencies
npm install
```

### Run Development Server

**IMPORTANT:** You must use `cargo tauri dev`, not just `npm run dev`

```bash
# This launches the Tauri desktop app
cargo tauri dev
```

This command will:
1. Start the Vite dev server on port 5174
2. Build the Rust backend
3. Launch the native desktop window

### Why not just `npm run dev`?

Running `npm run dev` alone only starts the web server without the Tauri runtime. The app requires Tauri's backend to:
- Load governance data from the filesystem
- Execute validation commands
- Query goals and decisions

**You will see errors** if you open `http://localhost:5174` directly in a browser.

## Build Production

```bash
# Build the production desktop app
npm run build
cargo tauri build
```

The app will be in: `src-tauri/target/release/`

## Configuration

The app looks for the governance folder at:

1. Environment variable: `$AEQUITAS_GOVERNANCE`
2. Default: `$HOME/Documents/workfolder/aequitas/governance`

Set custom path:
```bash
export AEQUITAS_GOVERNANCE=/path/to/governance
cargo tauri dev
```

## Project Structure

```
meta-gui/
├── src/                    # Svelte frontend
│   ├── App.svelte         # Main app + navigation
│   ├── main.js            # Entry point
│   ├── app.css            # Global styles
│   └── lib/               # Components
│       ├── Dashboard.svelte
│       ├── GoalExplorer.svelte
│       └── AuditViewer.svelte
├── src-tauri/             # Rust backend
│   ├── src/
│   │   ├── main.rs        # Tauri app
│   │   ├── commands.rs    # Command handlers
│   │   └── state.rs       # App state
│   └── tauri.conf.json    # Tauri config
├── package.json
├── vite.config.js
└── tailwind.config.js
```

## Features

- **Dashboard** — Overview of governance health
- **Goal Explorer** — Browse and filter goals
- **Audit Viewer** — Validation results

## Troubleshooting

### Error: "Tauri is not available"

**Cause:** You're running in a browser, not the Tauri app.

**Solution:** Use `cargo tauri dev` instead of `npm run dev`

### Error: "Governance folder not found"

**Cause:** The governance path is incorrect.

**Solution:** Set `AEQUITAS_GOVERNANCE` environment variable:
```bash
export AEQUITAS_GOVERNANCE=/absolute/path/to/governance
cargo tauri dev
```

### Port 5174 already in use

**Cause:** Another process is using port 5174.

**Solution:** Change port in `vite.config.js` and `src-tauri/tauri.conf.json`
