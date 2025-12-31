use std::path::PathBuf;
use surrealdb::Surreal;
use surrealdb::engine::local::{Db, SurrealKv};
use crate::errors::{MetaError, Result};

pub mod migration;

pub struct SurrealStore {
    pub db: Surreal<Db>,
}

impl SurrealStore {
    /// Initialize the SurrealDB store at the given path
    pub async fn init(path: PathBuf) -> Result<Self> {
        let db = Surreal::new::<SurrealKv>(path).await
            .map_err(|e| MetaError::SystemError(format!("Failed to init DB: {}", e)))?;
        
        db.use_ns("aequitas").use_db("metatheos").await
            .map_err(|e| MetaError::SystemError(format!("Failed to select DB: {}", e)))?;
        
        // --- Schema Definition ---
        
        // Daily Notes
        // We use string for date ID? daily_notes:2023-10-27
        // We use string for date ID? daily_notes:2023-10-27
        let _ = db.query("DEFINE TABLE daily_notes SCHEMAFULL").await;
        let _ = db.query("DEFINE FIELD date ON TABLE daily_notes TYPE string ASSERT $value != NONE").await;
        let _ = db.query("DEFINE FIELD content ON TABLE daily_notes TYPE string").await;
        // Dynamic fields will just be stored as top-level fields in the JSON document, 
        // which SCHEMAFULL allows if we define them, or SCHEMALESS? 
        // Let's use SCHEMALESS for now to support dynamic frontmatter without explicit definitions for every user field.
        // Actually, for "dynamic management", SCHEMALESS is better for the user's custom fields.
        
        // Let's redefine as SCHEMALESS for maximum flexibility as requested.
        let _ = db.query("DEFINE TABLE daily_notes SCHEMALESS").await;

        // Goals
        let _ = db.query("DEFINE TABLE goals SCHEMALESS").await;
        // We can enforce some structure later if needed, but SCHEMALESS fits "Markdown frontmatter" paradigm best.

        Ok(Self { db })
    }

    pub fn get_db(&self) -> &Surreal<Db> {
        &self.db
    }
}
