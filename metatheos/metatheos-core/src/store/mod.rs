use std::path::PathBuf;
use surrealdb::Surreal;
use surrealdb::engine::local::{Db, SurrealKv};
use crate::errors::{MetaError, Result};
use chrono::NaiveDate;
use crate::DailyNote;

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

    pub async fn get_daily_note(&self, date: NaiveDate) -> Result<Option<DailyNote>> {
        let id = format!("daily_notes:{}", date.format("%Y-%m-%d"));
        let notes: Vec<DailyNote> = self.db.select((&id)).await
            .map_err(|e| MetaError::SystemError(format!("DB Select Error: {}", e)))?;
        Ok(notes.into_iter().next())
    }

    pub async fn save_daily_note(&self, note: DailyNote) -> Result<()> {
        let id = format!("daily_notes:{}", note.date.format("%Y-%m-%d"));
        // Update returns Vec<T>
        let _: Vec<DailyNote> = self.db.update((&id))
            .content(note)
            .await
            .map_err(|e| MetaError::SystemError(format!("DB Save Error: {}", e)))?;
        Ok(())
    }

    // === Dashboard Query Methods ===

    /// Get all goals from the database
    pub async fn get_all_goals(&self) -> Result<Vec<crate::Goal>> {
        let goals: Vec<crate::Goal> = self.db
            .select("goals")
            .await
            .map_err(|e| MetaError::SystemError(format!("Failed to query goals: {}", e)))?;
        Ok(goals)
    }

    /// Get all phases from the database
    pub async fn get_all_phases(&self) -> Result<Vec<crate::Phase>> {
        let phases: Vec<crate::Phase> = self.db
            .select("phases")
            .await
            .map_err(|e| MetaError::SystemError(format!("Failed to query phases: {}", e)))?;
        Ok(phases)
    }

    /// Get all daily notes from the database
    pub async fn get_all_daily_notes(&self) -> Result<Vec<DailyNote>> {
        let notes: Vec<DailyNote> = self.db
            .select("daily_notes")
            .await
            .map_err(|e| MetaError::SystemError(format!("Failed to query daily notes: {}", e)))?;
        Ok(notes)
    }

    /// Count goals by status using SurrealDB query
    pub async fn count_goals_by_status(&self) -> Result<std::collections::HashMap<String, usize>> {
        use serde::Deserialize;

        #[derive(Deserialize)]
        struct StatusCount {
            status: String,
            count: i64,
        }

        let query = "SELECT status, count() as count FROM goals GROUP BY status";
        let mut response = self.db
            .query(query)
            .await
            .map_err(|e| MetaError::SystemError(format!("Status count query failed: {}", e)))?;

        let counts: Vec<StatusCount> = response
            .take(0)
            .map_err(|e| MetaError::SystemError(format!("Failed to parse status counts: {}", e)))?;

        let mut result = std::collections::HashMap::new();
        for count in counts {
            result.insert(count.status, count.count as usize);
        }
        Ok(result)
    }

    /// Get goals filtered by status
    pub async fn get_goals_by_status(&self, status: &str) -> Result<Vec<crate::Goal>> {
        let query = format!("SELECT * FROM goals WHERE status = '{}'", status);
        let mut response = self.db
            .query(&query)
            .await
            .map_err(|e| MetaError::SystemError(format!("Goals by status query failed: {}", e)))?;

        let goals: Vec<crate::Goal> = response
            .take(0)
            .map_err(|e| MetaError::SystemError(format!("Failed to parse goals: {}", e)))?;

        Ok(goals)
    }

    /// Get daily notes within a date range
    pub async fn get_daily_notes_in_range(&self, start: NaiveDate, end: NaiveDate) -> Result<Vec<DailyNote>> {
        let query = format!(
            "SELECT * FROM daily_notes WHERE date >= '{}' AND date <= '{}' ORDER BY date ASC",
            start.format("%Y-%m-%d"),
            end.format("%Y-%m-%d")
        );

        let mut response = self.db
            .query(&query)
            .await
            .map_err(|e| MetaError::SystemError(format!("Daily notes range query failed: {}", e)))?;

        let notes: Vec<DailyNote> = response
            .take(0)
            .map_err(|e| MetaError::SystemError(format!("Failed to parse daily notes: {}", e)))?;

        Ok(notes)
    }
}
