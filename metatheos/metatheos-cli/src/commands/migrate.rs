use anyhow::Result;
use std::path::Path;

pub fn run_migrate(root_path: &str) -> Result<()> {
    let root = Path::new(root_path);

    println!("🔄 Starting SurrealDB migration...");
    println!("📂 Governance root: {}", root.display());

    // Use tokio runtime to run async migration
    let runtime = tokio::runtime::Runtime::new()?;
    runtime.block_on(async {
        let db_path = root.join(".metatheos.db");

        // Delete existing database for fresh start
        if db_path.exists() {
            println!("🗑️  Removing existing database...");
            std::fs::remove_dir_all(&db_path)?;
        }

        println!("💾 Initializing SurrealDB at {}...", db_path.display());
        let store = metatheos_core::store::SurrealStore::init(db_path).await?;

        println!("\n📊 Running migration...\n");
        metatheos_core::store::migration::migrate_all(&store, root).await?;

        println!("\n✅ Migration complete!");
        Ok::<(), anyhow::Error>(())
    })?;

    Ok(())
}
