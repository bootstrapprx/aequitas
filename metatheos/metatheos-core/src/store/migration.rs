use crate::errors::Result;
use crate::store::SurrealStore;
use std::path::Path;

/// Migration is now a NO-OP.
/// The database is the single source of truth.
/// Use the GUI/CLI to create entities, or run SQL seed scripts directly.
pub async fn migrate_all(_store: &SurrealStore, _root: &Path) -> Result<()> {
    println!("Migration check: DB-only mode - no file migration");
    Ok(())
}
