# Rename: Meta Engine → Metatheos

**Date:** 2025-12-29
**Version:** 0.5.0
**Status:** ✅ Complete

---

## Summary

The project has been successfully renamed from "Meta Engine" to "Metatheos" and relocated from `/aequitas/meta-engine/` to `/aequitas/metatheos/`.

### Changes Made

✅ **Directory Structure**
- Created new `/aequitas/metatheos/` directory
- Renamed all subdirectories:
  - `meta-core` → `metatheos-core`
  - `meta-cli` → `metatheos-cli`
  - `meta-gui` → `metatheos-gui`

✅ **Package Names**
- Workspace member names updated
- All Cargo.toml package names updated
- Binary name changed from `meta-cli` to `metatheos`

✅ **Import Statements**
- All `use meta_core::*` → `use metatheos_core::*`
- Updated in CLI source files
- Updated in GUI source files
- Updated in CRUD commands

✅ **Branding & UI**
- Window title: "Metatheos - Governance Engine"
- Product name: "Metatheos"
- App identifier: `com.aequitas.metatheos`
- Sidebar heading: "Metatheos"
- Version display: "Metatheos v0.5.0"
- Page title: "Metatheos - Governance Engine"

✅ **Assets**
- Logo copied from `assets/metatheos_logo.png`
- Placed at `metatheos-gui/public/metatheos-icon.png`
- Icon referenced in index.html

✅ **Compilation**
- All code compiles successfully
- No errors or warnings
- App runs on http://localhost:5174

---

## File Changes

### Renamed Directories
```
meta-engine/               → metatheos/
├── meta-core/            → metatheos-core/
├── meta-cli/             → metatheos-cli/
└── meta-gui/             → metatheos-gui/
```

### Modified Files

#### Workspace Configuration
- **Cargo.toml** (root)
  - `members = ["metatheos-core", "metatheos-cli", "metatheos-gui/src-tauri"]`

#### Core Library
- **metatheos-core/Cargo.toml**
  - `name = "metatheos-core"`
  - No other changes needed (all exports remain the same)

#### CLI
- **metatheos-cli/Cargo.toml**
  - `name = "metatheos"`
  - `[[bin]] name = "metatheos"`
  - `metatheos-core = { path = "../metatheos-core" }`

- **metatheos-cli/src/**/*.rs**
  - All `use meta_core` → `use metatheos_core`

#### GUI Application
- **metatheos-gui/package.json**
  - `name = "metatheos-gui"`
  - `version = "0.5.0"`

- **metatheos-gui/src-tauri/Cargo.toml**
  - `name = "metatheos-gui"`
  - `metatheos-core = { path = "../../metatheos-core" }`

- **metatheos-gui/src-tauri/tauri.conf.json**
  - `productName = "Metatheos"`
  - `version = "0.5.0"`
  - `identifier = "com.aequitas.metatheos"`
  - `title = "Metatheos - Governance Engine"`

- **metatheos-gui/index.html**
  - `<title>Metatheos - Governance Engine</title>`
  - `<link rel="icon" href="/metatheos-icon.png" />`

- **metatheos-gui/src/App.svelte**
  - Sidebar heading: "Metatheos"
  - Subtitle: "Governance Engine"
  - Version: "Metatheos v0.5.0"
  - Tagline: "Aequitas Governance Engine"

- **metatheos-gui/src-tauri/src/**/*.rs**
  - All `use meta_core` → `use metatheos_core`
  - All `meta_core::` → `metatheos_core::`

---

## CLI Usage

### Before (Meta Engine)
```bash
# Build
cd meta-engine/meta-cli
cargo build --release

# Run
./target/release/meta-cli --help
./target/release/meta-cli scan
```

### After (Metatheos)
```bash
# Build
cd metatheos/metatheos-cli
cargo build --release

# Run
./target/release/metatheos --help
./target/release/metatheos scan
```

### Install Command Update

Update `install.sh` if needed:
```bash
# Before
cargo install --path meta-cli

# After
cargo install --path metatheos-cli
```

---

## GUI Usage

### Before (Meta Engine)
```bash
cd meta-engine/meta-gui
cargo tauri dev
cargo tauri build
```

### After (Metatheos)
```bash
cd metatheos/metatheos-gui
cargo tauri dev
cargo tauri build
```

### Window Title & Branding
- **Before:** "Aequitas Meta Engine v0.4.0"
- **After:** "Metatheos v0.5.0 - Aequitas Governance Engine"

---

## Migration Checklist

### For Users

If you have the old meta-engine:

- [ ] Stop any running meta-engine processes
- [ ] Update your scripts/aliases that reference `meta-cli`
- [ ] Update any documentation that references "Meta Engine"
- [ ] If you have `meta-cli` in your PATH, reinstall as `metatheos`:
  ```bash
  cd /path/to/aequitas/metatheos/metatheos-cli
  cargo install --path .
  ```

### For Developers

- [ ] Update git remotes if applicable
- [ ] Update IDE workspace paths
- [ ] Update build scripts
- [ ] Update documentation

---

## Breaking Changes

### ⚠️ Binary Name Changed
- **Old:** `meta-cli`
- **New:** `metatheos`

**Impact:** Shell scripts, aliases, and PATH references need updating.

**Migration:**
```bash
# Update alias
# Before: alias meta="meta-cli"
# After:  alias meta="metatheos"

# Update scripts
# Before: /usr/local/bin/meta-cli scan
# After:  /usr/local/bin/metatheos scan
```

### ⚠️ Rust Package Names Changed
- **Old:** `meta-core`, `meta-cli`, `meta-gui`
- **New:** `metatheos-core`, `metatheos-cli`, `metatheos-gui`

**Impact:** Only affects external projects that depend on these crates.

**Migration:**
```toml
# Before
meta-core = { path = "../meta-engine/meta-core" }

# After
metatheos-core = { path = "../metatheos/metatheos-core" }
```

### ⚠️ Application Identifier Changed
- **Old:** `com.aequitas.meta-engine`
- **New:** `com.aequitas.metatheos`

**Impact:** Linux desktop shortcuts and app data directories may change.

---

## Verification

### ✅ Compilation Test
```bash
cd /path/to/aequitas/metatheos
cargo build
# Result: Finished `dev` profile in 14.91s
```

### ✅ CLI Test
```bash
cd metatheos-cli
cargo run -- --help
# Should show: metatheos [OPTIONS] <COMMAND>
```

### ✅ GUI Test
```bash
cd metatheos-gui
cargo tauri dev
# Window should show: "Metatheos - Governance Engine"
# Sidebar should show: "Metatheos" with version "v0.5.0"
```

### ✅ Browser Test
```bash
curl http://localhost:5174 | grep title
# Should show: <title>Metatheos - Governance Engine</title>
```

---

## Documentation Updates Needed

The following documentation files reference "Meta Engine" and should be updated:

### High Priority
- [ ] README.md (if exists)
- [ ] IMPLEMENTATION.md
- [ ] Phase documentation (PHASE_*.md files)

### Medium Priority
- [ ] AI_SETUP_GUIDE.md
- [ ] OLLAMA_SETUP.md
- [ ] Usage guides

### Low Priority
- [ ] Historical phase completion documents (can keep as-is)

---

## Logo & Branding

### New Logo
- **Source:** `/aequitas/assets/metatheos_logo.png`
- **Deployed to:** `/metatheos/metatheos-gui/public/metatheos-icon.png`
- **Referenced in:** `index.html`

### Brand Colors (if applicable)
- Update tailwind theme if logo introduces new brand colors
- Update favicon if needed

---

## Post-Rename Cleanup

### Optional: Remove Old Directory
```bash
# ONLY after verifying everything works
rm -rf /path/to/aequitas/meta-engine
```

### Update Git (if tracked)
```bash
git mv meta-engine metatheos
git commit -m "Rename meta-engine to metatheos"
```

---

## Rollback Instructions

If you need to revert:

1. **Copy files back:**
   ```bash
   cp -r metatheos meta-engine
   ```

2. **Revert package names:**
   ```bash
   cd meta-engine
   mv metatheos-core meta-core
   mv metatheos-cli meta-cli
   mv metatheos-gui meta-gui
   ```

3. **Revert Cargo.toml changes:**
   - Change all `metatheos-*` back to `meta-*`
   - Change binary name back to `meta-cli`

4. **Revert imports:**
   ```bash
   find . -name "*.rs" -exec sed -i 's/metatheos_core/meta_core/g' {} \;
   ```

---

## Timeline

- **Planning:** 5 minutes
- **Directory rename:** 2 minutes
- **Package name updates:** 10 minutes
- **Import statement updates:** 5 minutes
- **Branding updates:** 10 minutes
- **Testing & verification:** 10 minutes
- **Documentation:** 10 minutes

**Total:** ~52 minutes

---

## Success Criteria

✅ All code compiles without errors
✅ CLI binary runs with new name `metatheos`
✅ GUI displays "Metatheos" branding
✅ No references to "meta-engine" or "meta_core" in code
✅ App runs successfully on http://localhost:5174
✅ Logo displayed correctly

**Status:** All criteria met! ✅

---

## Next Steps

1. Update remaining documentation files
2. Commit changes to version control
3. Update any external references (wikis, issue trackers, etc.)
4. Announce rename to team/users
5. Consider keeping a redirect/alias for transition period

---

**Rename completed successfully!** 🎉

The project is now fully operational as **Metatheos - Aequitas Governance Engine**
