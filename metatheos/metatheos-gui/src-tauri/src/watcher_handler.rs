use metatheos_core::{FileChangeEvent, EntityType, ChangeKind, GovernanceContext};
use metatheos_core::store::SurrealStore;
use metatheos_core::parser::MarkdownParser;
use std::sync::Arc;
use std::path::{Path, PathBuf};
use tauri::{AppHandle, Emitter};

/// Handle a file change event by updating the DB cache and emitting frontend events
pub async fn handle_file_change(
    event: FileChangeEvent,
    store: Arc<SurrealStore>,
    governance_root: PathBuf,
    app: AppHandle,
) {
    let result = match event.kind {
        ChangeKind::Create | ChangeKind::Modify => {
            handle_create_or_modify(&event, &store, &governance_root).await
        }
        ChangeKind::Delete => {
            handle_delete(&event, &store).await
        }
    };

    // Log errors but don't crash the watcher
    if let Err(e) = result {
        eprintln!("File watcher error handling {:?}: {}", event.path, e);
    }

    // Emit event to frontend
    let entity_type_str = match event.entity_type {
        EntityType::Goal => "goal",
        EntityType::Phase => "phase",
        EntityType::Audit => "audit",
        EntityType::Prompt => "prompt",
        EntityType::DailyNote => "daily_note",
        EntityType::Decision => "decision",
        EntityType::Canon => "canon",
        EntityType::Unknown => "unknown",
    };

    // Emit specific entity change event
    if let Err(e) = app.emit(&format!("{}_changed", entity_type_str), &event.path) {
        eprintln!("Failed to emit event: {}", e);
    }

    // Also emit a general governance_changed event
    if let Err(e) = app.emit("governance_changed", entity_type_str) {
        eprintln!("Failed to emit governance_changed event: {}", e);
    }
}

/// Handle create or modify events
async fn handle_create_or_modify(
    event: &FileChangeEvent,
    store: &Arc<SurrealStore>,
    governance_root: &Path,
) -> Result<(), Box<dyn std::error::Error>> {
    match event.entity_type {
        EntityType::Goal => refresh_goal(&event.path, store).await?,
        EntityType::Phase => refresh_all_phases(governance_root, store).await?,
        EntityType::Audit => refresh_audit(&event.path, store).await?,
        EntityType::Prompt => refresh_prompt(&event.path, store).await?,
        EntityType::DailyNote => refresh_daily_note(&event.path, store).await?,
        EntityType::Canon => {
            // Canon files are read-only, just emit notification
            println!("Canon file changed: {:?}", event.path);
        }
        _ => {
            // Unknown or other types - just log
            println!("File changed: {:?}", event.path);
        }
    }

    Ok(())
}

/// Handle delete events
async fn handle_delete(
    event: &FileChangeEvent,
    store: &Arc<SurrealStore>,
) -> Result<(), Box<dyn std::error::Error>> {
    // Extract ID from path
    let id = extract_id_from_path(&event.path);

    match event.entity_type {
        EntityType::Goal => {
            if let Some(goal_id) = id {
                let _: Option<metatheos_core::Goal> = store
                    .get_db()
                    .delete(("goals", goal_id.as_str()))
                    .await?;
            }
        }
        EntityType::Phase => {
            if let Some(phase_id) = id {
                let _: Option<metatheos_core::Phase> = store
                    .get_db()
                    .delete(("phases", phase_id.as_str()))
                    .await?;
            }
        }
        EntityType::Audit => {
            if let Some(audit_id) = id {
                let _: Option<metatheos_core::Audit> = store
                    .get_db()
                    .delete(("audits", audit_id.as_str()))
                    .await?;
            }
        }
        EntityType::Prompt => {
            if let Some(prompt_id) = id {
                let _: Option<metatheos_core::Prompt> = store
                    .get_db()
                    .delete(("prompts", prompt_id.as_str()))
                    .await?;
            }
        }
        EntityType::DailyNote => {
            if let Some(date) = id {
                let _: Option<metatheos_core::DailyNote> = store
                    .get_db()
                    .delete(("daily_notes", date.as_str()))
                    .await?;
            }
        }
        _ => {
            println!("Deleted file: {:?}", event.path);
        }
    }

    Ok(())
}

/// Refresh a goal from its markdown file
async fn refresh_goal(
    path: &Path,
    store: &Arc<SurrealStore>,
) -> Result<(), Box<dyn std::error::Error>> {
    match MarkdownParser::parse_goal(path) {
        Ok(goal) => {
            let goal_id = goal.goal_id.clone();
            let _: Option<metatheos_core::Goal> = store
                .get_db()
                .update(("goals", goal_id.as_str()))
                .content(goal)
                .await?;
            println!("Refreshed goal: {}", goal_id);
        }
        Err(e) => {
            eprintln!("Failed to parse goal at {:?}: {}", path, e);
            // Don't delete from DB on parse error - keep existing data
        }
    }

    Ok(())
}

/// Refresh all phases (needed when one phase file changes, as it may affect others)
async fn refresh_all_phases(
    governance_root: &Path,
    store: &Arc<SurrealStore>,
) -> Result<(), Box<dyn std::error::Error>> {
    match GovernanceContext::load(governance_root) {
        Ok(ctx) => {
            for phase in ctx.all_phases() {
                let _: Option<metatheos_core::Phase> = store
                    .get_db()
                    .update(("phases", phase.phase_id.as_str()))
                    .content(phase.clone())
                    .await?;
            }
            println!("Refreshed all phases");
        }
        Err(e) => {
            eprintln!("Failed to load governance context for phase refresh: {}", e);
        }
    }

    Ok(())
}

/// Refresh an audit from its markdown file
async fn refresh_audit(
    path: &Path,
    store: &Arc<SurrealStore>,
) -> Result<(), Box<dyn std::error::Error>> {
    match MarkdownParser::parse_audit(path) {
        Ok(audit) => {
            // Use file stem as ID
            if let Some(stem) = path.file_stem() {
                let audit_id = stem.to_string_lossy().to_string();
                let _: Option<metatheos_core::Audit> = store
                    .get_db()
                    .update(("audits", audit_id.as_str()))
                    .content(audit)
                    .await?;
                println!("Refreshed audit: {}", audit_id);
            }
        }
        Err(e) => {
            eprintln!("Failed to parse audit at {:?}: {}", path, e);
        }
    }

    Ok(())
}

/// Refresh a prompt from its markdown file
async fn refresh_prompt(
    path: &Path,
    store: &Arc<SurrealStore>,
) -> Result<(), Box<dyn std::error::Error>> {
    match MarkdownParser::parse_prompt(path) {
        Ok(prompt) => {
            // Use file stem as ID
            if let Some(stem) = path.file_stem() {
                let prompt_id = stem.to_string_lossy().to_string();
                let _: Option<metatheos_core::Prompt> = store
                    .get_db()
                    .update(("prompts", prompt_id.as_str()))
                    .content(prompt)
                    .await?;
                println!("Refreshed prompt: {}", prompt_id);
            }
        }
        Err(e) => {
            eprintln!("Failed to parse prompt at {:?}: {}", path, e);
        }
    }

    Ok(())
}

/// Refresh a daily note from its markdown file
async fn refresh_daily_note(
    path: &Path,
    store: &Arc<SurrealStore>,
) -> Result<(), Box<dyn std::error::Error>> {
    match MarkdownParser::parse_daily(path) {
        Ok(note) => {
            let date_str = note.date.format("%Y-%m-%d").to_string();
            let _: Option<metatheos_core::DailyNote> = store
                .get_db()
                .update(("daily_notes", date_str.as_str()))
                .content(note)
                .await?;
            println!("Refreshed daily note: {}", date_str);
        }
        Err(e) => {
            eprintln!("Failed to parse daily note at {:?}: {}", path, e);
        }
    }

    Ok(())
}

/// Extract ID from file path
/// For goals: extract G-XXX from filename
/// For phases: extract PHASE_X or phase ID from frontmatter
/// For audits/prompts/daily notes: use file stem
fn extract_id_from_path(path: &Path) -> Option<String> {
    if let Some(stem) = path.file_stem() {
        let stem_str = stem.to_string_lossy().to_string();

        // For goals, extract G-XXX pattern
        if stem_str.starts_with("G-") {
            if let Some(end_idx) = stem_str.find('_') {
                return Some(stem_str[..end_idx].to_string());
            }
            return Some(stem_str);
        }

        // For daily notes, it's just the date (YYYY-MM-DD)
        if stem_str.contains('-') && stem_str.len() == 10 {
            return Some(stem_str);
        }

        // For everything else, use the full stem
        return Some(stem_str);
    }

    None
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_extract_id_from_goal_path() {
        let path = PathBuf::from("governance/03_GOALS_EPICS/G-042_test_goal.md");
        let id = extract_id_from_path(&path);
        assert_eq!(id, Some("G-042".to_string()));
    }

    #[test]
    fn test_extract_id_from_daily_path() {
        let path = PathBuf::from("governance/01_DAILY/2025-12-31.md");
        let id = extract_id_from_path(&path);
        assert_eq!(id, Some("2025-12-31".to_string()));
    }

    #[test]
    fn test_extract_id_from_audit_path() {
        let path = PathBuf::from("governance/05_AUDITS/AUDIT_001.md");
        let id = extract_id_from_path(&path);
        assert_eq!(id, Some("AUDIT_001".to_string()));
    }
}
