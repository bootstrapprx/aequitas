use crate::errors::Result;
use crate::parser::MarkdownParser;
use crate::store::SurrealStore;
use std::path::Path;
use walkdir::WalkDir;

pub async fn migrate_all(store: &SurrealStore, root: &Path) -> Result<()> {
    println!("Starting migration checks...");

    // Helper to check if a table is empty
    let is_empty = |table: &str| {
        let db = store.db.clone();
        let table = table.to_string();
        async move {
            let sql = format!("SELECT count() FROM {} GROUP ALL", table);
            let count: Option<i64> = db.query(sql)
                .await
                .ok()
                .and_then(|mut r| r.take(0).ok())
                .and_then(|v: Option<i64>| v);
            count.unwrap_or(0) == 0
        }
    };

    // DAILY
    if is_empty("daily_notes").await {
        println!("Migrating daily_notes...");
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
    }

    // GOALS
    if is_empty("goals").await {
        println!("Migrating goals...");
        let goals_dir = root.join("03_GOALS_EPICS");
        if goals_dir.exists() {
            let mut success_count = 0;
            let mut fail_count = 0;
            for entry in WalkDir::new(&goals_dir).into_iter().filter_map(|e| e.ok()) {
                if entry.path().extension().map_or(false, |e| e == "md") {
                    match MarkdownParser::parse_goal(entry.path()) {
                        Ok(goal) => {
                            let id = format!("goals:{}", goal.goal_id);
                            match store.db.create::<Option<crate::Goal>>(&id).content(goal.clone()).await {
                                Ok(_) => {
                                    success_count += 1;
                                    println!("  ✓ Migrated goal: {}", goal.goal_id);
                                },
                                Err(e) => {
                                    fail_count += 1;
                                    eprintln!("  ✗ Failed to create goal {}: {}", goal.goal_id, e);
                                }
                            }
                        },
                        Err(e) => {
                            fail_count += 1;
                            eprintln!("  ✗ Failed to parse goal {:?}: {}", entry.path(), e);
                        }
                    }
                }
            }
            println!("Goals migration complete: {} success, {} failed", success_count, fail_count);
        }
    }

    // PHASES
    if is_empty("phases").await {
        println!("Migrating phases...");
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
    }
    
    // AUDITS
    if is_empty("audits").await {
        println!("Migrating audits...");
        let audits_dir = root.join("05_AUDITS");
        if audits_dir.exists() {
            for entry in WalkDir::new(&audits_dir).into_iter().filter_map(|e| e.ok()) {
                 if entry.path().extension().map_or(false, |e| e == "md") {
                    if let Ok(audit) = MarkdownParser::parse_audit(entry.path()) {
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
    }

    // DECISIONS
    if is_empty("decisions").await {
        println!("Migrating decisions...");
        let decisions_dir = root.join("04_DECISIONS");
        if decisions_dir.exists() {
            for entry in WalkDir::new(&decisions_dir).into_iter().filter_map(|e| e.ok()) {
                 if entry.path().extension().map_or(false, |e| e == "md") {
                    if let Ok(decision) = MarkdownParser::parse_decision(entry.path()) {
                        let id = format!("decisions:{}", decision.decision_id);
                        let _: std::result::Result<Option<crate::Decision>, _> = store.db
                            .create(&id)
                            .content(decision)
                            .await;
                    }
                }
            }
        }
    }

    // PROMPTS
    if is_empty("prompts").await {
        println!("Migrating prompts...");
        let prompts_dir = root.join("06_PROMPTS/library");
        if prompts_dir.exists() {
            for entry in WalkDir::new(&prompts_dir).into_iter().filter_map(|e| e.ok()) {
                 if entry.path().extension().map_or(false, |e| e == "md") {
                    if let Ok(prompt) = MarkdownParser::parse_prompt(entry.path()) {
                        let stem = entry.path().file_stem().unwrap().to_string_lossy();
                        let id = format!("prompts:{}", stem);
                        let _: std::result::Result<Option<crate::Prompt>, _> = store.db
                            .create(&id)
                            .content(prompt)
                            .await;
                    }
                }
            }
        }
    }

    println!("Migration complete.");
    Ok(())
}
