use crate::errors::Result;
use crate::parser::MarkdownParser;
use crate::store::SurrealStore;
use std::path::Path;
use walkdir::WalkDir;

pub async fn migrate_all(store: &SurrealStore, root: &Path) -> Result<()> {
    // Check if empty
    let existing: Option<i64> = store.db.query("SELECT count() FROM goals GROUP ALL")
        .await
        .ok()
        .and_then(|mut r| r.take(0).ok())
        .and_then(|v: Option<i64>| v);

    if let Some(count) = existing {
        if count > 0 {
            println!("DB likely populated ({} goals), skipping full migration.", count);
            return Ok(());
        }
    }

    println!("Starting migration from FS at {:?}", root);

    // DAILY
    let daily_dir = root.join("01_DAILY");
    if daily_dir.exists() {
        for entry in WalkDir::new(&daily_dir).into_iter().filter_map(|e| e.ok()) {
            if entry.path().extension().map_or(false, |e| e == "md") {
                if let Ok(note) = MarkdownParser::parse_daily(entry.path()) {
                    let id = format!("daily_notes:{}", note.date.format("%Y-%m-%d"));
                    let _: std::result::Result<Option<crate::DailyNote>, _> = store.db
                        .create(&id)
                        .content(note)
                        .await;
                }
            }
        }
    }

    // GOALS (03_GOALS_EPICS directory)
    let goals_dir = root.join("03_GOALS_EPICS");
    if goals_dir.exists() {
        for entry in WalkDir::new(&goals_dir).into_iter().filter_map(|e| e.ok()) {
            if entry.path().extension().map_or(false, |e| e == "md") {
                if let Ok(goal) = MarkdownParser::parse_goal(entry.path()) {
                     // ID likely "goals:G-25-..."
                     let id = format!("goals:{}", goal.goal_id);
                     let _: std::result::Result<Option<crate::Goal>, _> = store.db
                        .create(&id)
                        .content(goal)
                        .await;
                }
            }
        }
    }

    // PHASES (02_PHASES directory)
    let phases_dir = root.join("02_PHASES");
    if phases_dir.exists() {
         for entry in WalkDir::new(&phases_dir).into_iter().filter_map(|e| e.ok()) {
            let fname = entry.file_name().to_string_lossy();
            if fname.starts_with("PHASE") && fname.ends_with(".md") {
                if let Ok(phase) = MarkdownParser::parse_phase(entry.path()) {
                     let id = format!("phases:{}", phase.phase_id);
                     let _: std::result::Result<Option<crate::Phase>, _> = store.db
                        .create(&id)
                        .content(phase)
                        .await;
                }
            }
        }
    }
    
    // AUDITS
    let audits_dir = root.join("05_AUDITS");
    if audits_dir.exists() {
        for entry in WalkDir::new(&audits_dir).into_iter().filter_map(|e| e.ok()) {
             if entry.path().extension().map_or(false, |e| e == "md") {
                if let Ok(audit) = MarkdownParser::parse_audit(entry.path()) {
                    // Use file stem for ID
                    let stem = entry.path().file_stem().unwrap().to_string_lossy();
                    let id = format!("audits:{}", stem);
                    let _: std::result::Result<Option<crate::AuditRecord>, _> = store.db
                        .create(&id)
                        .content(audit)
                        .await;
                }
            }
        }
    }

    println!("Migration complete.");
    Ok(())
}
