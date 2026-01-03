#!/usr/bin/env rust-script
//! ```cargo
//! [dependencies]
//! surrealdb = "1.5"
//! tokio = { version = "1", features = ["full"] }
//! serde = { version = "1", features = ["derive"] }
//! serde_json = "1"
//! anyhow = "1"
//! ```

use anyhow::Result;
use serde_json::json;
use std::path::Path;

#[tokio::main]
async fn main() -> Result<()> {
    println!("🌱 Seeding phases into SurrealDB...\n");

    let db_path = "/home/actpm/Documents/workfolder/aequitas/governance/.metatheos.db";
    
    // Connect to SurrealDB
    let db = surrealdb::Surreal::new::<surrealdb::engine::local::RocksDb>(db_path).await?;
    db.use_ns("metatheos").use_db("governance").await?;

    // Define phases with their data
    let phases = vec![
        ("P0", "Canon & Kernel", "done", "2025-01-01", "2025-06-30"),
        ("P1", "Foundation", "done", "2025-07-01", "2025-09-30"),
        ("P2", "Mapping", "done", "2025-10-01", "2025-10-31"),
        ("P3", "Chart Generation", "done", "2025-11-01", "2025-11-30"),
        ("P4", "Accounting Core", "done", "2025-10-01", "2025-12-31"),
        ("P5", "Financial Events Layer", "active", "2026-01-01", "2026-03-31"),
        ("P6", "Operational Modules", "planned", "2026-04-01", "2026-06-30"),
        ("P7", "Intelligence (Dexter)", "active", "2025-11-01", "2026-06-30"),
        ("P8", "Testing & Hardening", "active", "2026-01-01", "2026-06-30"),
    ];

    for (id, title, status, start, target) in phases {
        let content = json!({
            "phase_id": id,
            "title": title,
            "status": status,
            "start_date": start,
            "target_date": target,
            "dependencies": Vec::<String>::new(),
            "file_path": format!("/home/actpm/Documents/workfolder/aequitas/governance_archive/2026-01-02/02_PHASES/Phase {} — {}.md", 
                                 id.trim_start_matches('P'), title),
            "content": ""
        });

        match db.create(("phases", id)).content(content).await {
            Ok(_) => println!("  ✓ Seeded phase: {}", id),
            Err(e) => println!("  ✗ Failed to seed {}: {}", id, e),
        }
    }

    println!("\n✅ Phase seeding complete!");
    Ok(())
}
