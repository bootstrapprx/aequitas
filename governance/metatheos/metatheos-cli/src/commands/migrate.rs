use anyhow::Result;
use metatheos_core::store::SurrealStore;
use serde_json::json;
use std::path::Path;

pub fn run_migrate(root_path: &str) -> Result<()> {
    println!("🔧 Running migration: Seeding phases into database...\n");

    // Run async migration
    tokio::runtime::Runtime::new()?.block_on(async { seed_phases(root_path).await })
}

async fn seed_phases(root_path: &str) -> Result<()> {
    let root = Path::new(root_path);
    let db_path = root.join(".metatheos.db");

    let store = SurrealStore::init(db_path).await?;

    // Define all phases with correct data
    let phases = vec![
        ("P0", "Canon & Kernel", "done", "2025-01-01", "2025-06-30"),
        ("P1", "Foundation", "done", "2025-07-01", "2025-09-30"),
        ("P2", "Mapping", "done", "2025-10-01", "2025-10-31"),
        ("P3", "Chart Generation", "done", "2025-11-01", "2025-11-30"),
        ("P4", "Accounting Core", "done", "2025-10-01", "2025-12-31"),
        (
            "P5",
            "Financial Events Layer",
            "active",
            "2026-01-01",
            "2026-03-31",
        ),
        (
            "P6",
            "Operational Modules",
            "planned",
            "2026-04-01",
            "2026-06-30",
        ),
        (
            "P7",
            "Intelligence (Dexter)",
            "active",
            "2025-11-01",
            "2026-06-30",
        ),
        (
            "P8",
            "Testing & Hardening",
            "active",
            "2026-01-01",
            "2026-06-30",
        ),
    ];

    for (id, title, status, start_date, target_date) in phases {
        let content = json!({
            "phase_id": id,
            "title": title,
            "status": status,
            "start_date": start_date,
            "target_date": target_date,
            "dependencies": Vec::<String>::new(),
            "file_path": format!("{}/governance_archive/2026-01-02/02_PHASES/Phase {} — {}.md",
                                 root_path,
                                 id.trim_start_matches('P'),
                                 title),
            "content": ""
        });

        match store
            .db
            .create::<Option<serde_json::Value>>(("phases", id))
            .content(content.clone())
            .await
        {
            Ok(_) => println!("  ✓ Seeded phase: {} - {}", id, title),
            Err(e) => {
                // Try update if create fails (already exists)
                match store
                    .db
                    .update::<Option<serde_json::Value>>(("phases", id))
                    .content(content)
                    .await
                {
                    Ok(_) => println!("  ↻ Updated phase: {} - {}", id, title),
                    Err(e2) => println!("  ✗ Failed to seed {}: {} / {}", id, e, e2),
                }
            }
        }
    }

    println!("\n✅ Phase seeding complete!");
    println!("🔄 Restart the application to load phases.");
    Ok(())
}
