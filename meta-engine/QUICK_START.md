# Meta Engine - Quick Start Guide

## Launch the App

```bash
cd /home/actpm/Documents/workfolder/aequitas/meta-engine/meta-gui
cargo tauri dev
```

**App will open at:** Desktop window (not browser)
**Dev server:** http://localhost:5174 (for reference only)

## What You Can Do

### 📊 Dashboard Tab
- View current phase and statistics
- See active and blocked goals count
- Check governance health (errors/warnings)
- **Create daily notes** with date picker

### 🎯 Goals Tab
- Browse all goals organized by phase and status
- Search and filter goals
- **Update goal status** with dropdown menu
- View goal details (ID, title, owner, dependencies)

### 🔍 Audit Tab
- Real-time validation results
- Errors, warnings, and info messages
- File paths for quick navigation

## Quick Actions

### Update a Goal Status
1. Go to **Goals** tab
2. Find your goal (use search if needed)
3. Click **"Change Status"** button
4. Select new status from dropdown
5. ✅ Toast confirms success

**Available Statuses:** planned, active, blocked, partial, done, archived

### Create a Daily Note
1. Go to **Dashboard** tab
2. Select date (defaults to today)
3. Click **"Create Daily Note"**
4. ✅ Toast shows file path
5. Open in Obsidian to edit

**File created:** `/governance/01_DAILY/YYYY-MM-DD.md`

## Keyboard Shortcuts

- **Ctrl+R** - Reload app (refresh governance data)
- **Ctrl+W** - Close window
- **Ctrl+Q** - Quit app

## Status Transition Rules

```
planned   →  active, blocked, partial, done
active    →  blocked, partial, done
blocked   →  active, partial, done
partial   →  active, blocked, done
done      →  archived
archived  →  done
```

Invalid transitions will show an error message.

## Common Issues

### Port 5174 in Use
```bash
pkill -f meta-gui
pkill -f "vite.*5174"
cargo tauri dev
```

### Governance Files Not Loading
- Check `/governance` folder exists
- Verify files have `.md` extension
- Check terminal for specific errors

### Status Update Fails
- Verify transition is allowed (see rules above)
- Check goal ID exists
- Look for error in toast notification

## File Locations

**Governance Root:** `/home/actpm/Documents/workfolder/aequitas/governance`

**Daily Notes:** `/governance/01_DAILY/`
**Goals:** `/governance/03_GOALS_EPICS/`
**Decisions:** `/governance/04_DECISIONS/`
**Phases:** `/governance/02_PHASES/`

## Integration with Obsidian

✅ **Fully Compatible**
- Edit files in Obsidian anytime
- Use Meta GUI for quick status updates
- Keep both open simultaneously
- Files sync instantly (same folder)

## Documentation

- **Usage Guide:** `PHASE_3_USAGE_GUIDE.md` (detailed instructions)
- **Technical Summary:** `PHASE_3_SUMMARY.md` (implementation details)
- **Full README:** `README.md` (complete documentation)

## Support

For issues or questions:
1. Check documentation above
2. Look for errors in terminal output
3. Verify file permissions and locations
4. Restart the app

---

**Version:** 0.3.0 (Phase 3 Complete)
**Status:** Production Ready ✅
