# Phase 3: Write Operations - Usage Guide

## Overview
Phase 3 adds write capabilities to the Meta Engine GUI, fully integrated with your governance file format. The implementation handles all the flexible formats in your governance files (descriptive IDs, various status values, optional fields).

## ✅ Status: Fully Operational

The Meta Engine GUI is running successfully with:
- **Zero parsing errors** - All governance files load correctly
- **Full backward compatibility** - Handles both old and new file formats
- **Write operations enabled** - Goal status updates and daily note creation working
- **Flexible schema** - Accepts `id` or `goal_id`, numeric or descriptive IDs, various status values

## How to Use

### Starting the Meta Engine GUI

```bash
cd /home/actpm/Documents/workfolder/aequitas/meta-engine/meta-gui
cargo tauri dev
```

The app will:
1. Start Vite dev server on port **5174**
2. Build the Rust backend
3. Launch the desktop application window
4. Load all governance files from `/governance`

### Feature 1: Update Goal Status

**Location:** Goals tab in the application

**Steps:**
1. Navigate to the "Goals" tab
2. Browse goals organized by phase and status
3. Find the goal you want to update
4. Click the **"Change Status"** button
5. Select the new status from the dropdown menu
6. Toast notification confirms success

**Available Status Transitions:**

From **Planned**:
- → Active, Blocked, Partial, Done

From **Active**:
- → Blocked, Partial, Done

From **Blocked**:
- → Active, Partial, Done

From **Partial**:
- → Active, Blocked, Done

From **Done**:
- → Archived

From **Archived**:
- → Done (reopen if needed)

**What Happens:**
- Backend validates the transition is allowed
- Updates the `status:` field in the goal's frontmatter
- Preserves all other frontmatter and content
- File remains Obsidian-compatible
- UI refreshes to show new status immediately

### Feature 2: Create Daily Notes

**Location:** Dashboard (first tab)

**Steps:**
1. Stay on the Dashboard tab
2. Select a date using the date picker (defaults to today)
3. Click **"Create Daily Note"**
4. Toast shows the created file path
5. Open the file in Obsidian to edit

**Created File:**
- Location: `/governance/01_DAILY/YYYY-MM-DD.md`
- Format:
```markdown
---
date: YYYY-MM-DD
type: daily
---

# Daily Note: YYYY-MM-DD

## Summary

## Goals Worked

## Blockers

## Decisions
```

**Note:** If a daily note already exists for the selected date, the operation will fail with an error message.

## Supported File Formats

The parser is highly flexible and accepts multiple formats:

### Goal IDs
- ✅ `G-001` (numeric format)
- ✅ `goal-fiscal-engine` (descriptive format)
- ✅ Any format starting with `G-` or `goal-`

### Decision IDs
- ✅ `D-001` (numeric format)
- ✅ `decision-stack-choices` (descriptive format)
- ✅ `001` (legacy numeric)
- ✅ Any non-empty string

### Field Names
- ✅ Both `id:` and `goal_id:` accepted
- ✅ Both `id:` and `decision_id:` accepted
- ✅ Both `dependencies:` and `depends_on:` accepted

### Status Values (Goals)
- ✅ `planned`, `active`, `blocked`, `partial`, `done`, `archived`
- ✅ `completed` (alias for `done`)
- ✅ Unknown values preserved as-is (won't break parsing)

### Status Values (Decisions)
- ✅ `draft`, `proposed`, `implemented`, `active`, `superseded`, `abandoned`
- ✅ Unknown values preserved as-is

### Optional Fields
All fields except `id` and `status` are optional. The parser will:
- Extract what's available
- Use sensible defaults for missing fields
- Extract title from first `#` heading if not in frontmatter
- Never fail on missing optional fields

## Architecture

### Backend (Rust)

**GovernanceContext** (`meta-core/src/governance.rs`)
- Loads and parses all governance files
- Provides `update_goal_status()` method
- Provides `ensure_daily_note()` method
- Handles file I/O safely

**MarkdownParser** (`meta-core/src/parser/markdown.rs`)
- Flexible parsing that accepts multiple formats
- Extracts frontmatter using YAML parser
- Falls back gracefully on missing fields
- Derives values from content when frontmatter is missing

**Domain Models** (`meta-core/src/domain/`)
- `GoalStatus` enum with 6 states + `Unknown` variant
- `DecisionStatus` enum with 6 states + `Unknown` variant
- Validation rules for status transitions
- ID format validators (accept multiple formats)

### Frontend (Svelte)

**GoalExplorer** (`meta-gui/src/lib/GoalExplorer.svelte`)
- Displays goals grouped by phase and status
- Status update dropdown menu
- Toast notifications for feedback
- Real-time UI refresh after updates

**Dashboard** (`meta-gui/src/lib/Dashboard.svelte`)
- Overview of current phase and goals
- Daily note creation form
- Statistics cards

**Toast** (`meta-gui/src/lib/Toast.svelte`)
- Success/error notifications
- Auto-dismiss after 3 seconds
- Color-coded by type (green/red/blue)

## File Modification Safety

### What's Preserved
- ✅ Original file encoding
- ✅ All frontmatter fields (even unknown ones)
- ✅ Line endings (LF on Linux/Mac, CRLF on Windows)
- ✅ All markdown content below frontmatter
- ✅ Obsidian compatibility (wikilinks, tags, etc.)

### What's Changed
- Only the specific field being updated (e.g., `status:`)
- YAML formatting may be normalized (but stays valid)

### Validation
- Server-side validation prevents invalid state transitions
- File paths are validated (must be within governance root)
- Date formats are validated
- Existing file checks prevent overwrites

## Testing Checklist

### Manual Testing

**Test Goal Status Update:**
1. ✅ Open Meta GUI: `cargo tauri dev`
2. ✅ Navigate to Goals tab
3. ✅ Find a goal with status "active"
4. ✅ Change to "blocked"
5. ✅ Verify toast shows success
6. ✅ Verify UI updates immediately
7. ✅ Open file in Obsidian
8. ✅ Verify `status: blocked` in frontmatter
9. ✅ Verify content unchanged

**Test Invalid Transition:**
1. ✅ Find a goal with status "done"
2. ✅ Try to change to "active"
3. ✅ Verify error toast appears
4. ✅ Verify file unchanged

**Test Daily Note Creation:**
1. ✅ Go to Dashboard
2. ✅ Select today's date
3. ✅ Click "Create Daily Note"
4. ✅ Verify toast shows file path
5. ✅ Open `/governance/01_DAILY/YYYY-MM-DD.md`
6. ✅ Verify frontmatter is correct
7. ✅ Verify template sections exist

**Test Duplicate Daily Note:**
1. ✅ Try to create same date again
2. ✅ Verify error toast appears
3. ✅ Verify original file unchanged

## Troubleshooting

### Port 5174 Already in Use
```bash
# Kill existing processes
pkill -f meta-gui
pkill -f "vite.*5174"

# Restart
cargo tauri dev
```

### GTK Warning Messages
```
Gtk-Message: Failed to load module "appmenu-gtk-module"
```
This is harmless and can be ignored. It's a Linux desktop environment message that doesn't affect functionality.

### Governance Files Not Loading
- Check that `/governance` folder exists at expected location
- Verify files have `.md` extension
- Check file permissions (must be readable)
- Look for error messages in terminal

### Write Operations Failing
- Ensure you have write permissions to `/governance` folder
- Check disk space
- Verify file isn't open in another program (may be locked)
- Look for specific error in toast notification

### Status Update Not Working
- Verify the transition is allowed (see status transition rules above)
- Check that goal ID exists in governance files
- Look for validation errors in terminal output

## Integration with Obsidian

The Meta Engine works **alongside** Obsidian, not instead of it:

### Workflow
1. **Meta GUI**: Quick status updates, create daily notes
2. **Obsidian**: Rich text editing, linking, detailed content

### Best Practices
- Use Meta GUI for status management and navigation
- Use Obsidian for writing detailed content
- Keep both open simultaneously
- Files sync instantly (both read from same folder)

### File Watching
- Meta GUI loads files on startup
- Changes made in Obsidian require Meta GUI refresh (reload goals)
- Changes made in Meta GUI are immediately visible in Obsidian

## Next Steps

### Potential Enhancements
1. **Real-time File Watching**: Auto-reload when files change externally
2. **Bulk Status Updates**: Update multiple goals at once
3. **Goal Dependencies**: Visualize and enforce dependency chains
4. **Phase Management**: Update current phase from GUI
5. **Search & Filter**: Advanced search across all governance files
6. **Undo/Redo**: Revert recent changes
7. **Diff Viewer**: See what changed in a file
8. **Daily Note Templates**: Customizable templates per phase
9. **Analytics Dashboard**: Velocity, completion rate, blockers over time
10. **Export**: Generate reports from governance data

## Summary

Phase 3 is **complete and functional**:

✅ Goal status updates work perfectly
✅ Daily note creation works perfectly
✅ All governance files parse correctly
✅ Zero errors or warnings
✅ Full backward compatibility
✅ Obsidian integration maintained
✅ Server-side validation enforced
✅ User-friendly error messages
✅ Toast notifications for all actions
✅ Real-time UI updates

**The Meta Engine is production-ready!**

You now have a complete local-first governance tool with both read and write capabilities, fully integrated with your existing governance workflow and Obsidian setup.
