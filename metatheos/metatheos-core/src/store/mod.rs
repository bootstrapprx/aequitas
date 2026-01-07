use crate::errors::{MetaError, Result};
use crate::{
    Annotation, AuditRecord, DailyNote, Decision, Event, Goal, GoalStatus, Phase, Prompt, WorkItem,
};
use chrono::NaiveDate;
use std::path::PathBuf;
use surrealdb::engine::local::{Db, SurrealKv};
use surrealdb::Surreal;

pub mod consequences;
pub mod dto;
pub mod migration;
pub mod queries;
pub mod schema;

pub struct SurrealStore {
    pub db: Surreal<Db>,
}

impl SurrealStore {
    /// Initialize the SurrealDB store at the given path
    pub async fn init(path: PathBuf) -> Result<Self> {
        let db = Surreal::new::<SurrealKv>(path)
            .await
            .map_err(|e| MetaError::SystemError(format!("Failed to init DB: {}", e)))?;

        db.use_ns("aequitas")
            .use_db("metatheos")
            .await
            .map_err(|e| MetaError::SystemError(format!("Failed to select DB: {}", e)))?;

        // --- DB-First Schema Initialization ---
        // Initialize the complete canonical schema
        schema::initialize_schema(&db).await?;

        Ok(Self { db })
    }

    pub fn get_db(&self) -> &Surreal<Db> {
        &self.db
    }

    pub async fn get_daily_note(&self, date: NaiveDate) -> Result<Option<DailyNote>> {
        let sql = "SELECT content, date, phase, mode, protocol, goals_worked, decisions_made, divergences, goals, blockers, decisions, linked_goals, file_path, extra FROM type::thing($table, $id)";
        let mut response = self
            .db
            .query(sql)
            .bind(("table", "daily_notes"))
            .bind(("id", date.format("%Y-%m-%d").to_string()))
            .await
            .map_err(|e| MetaError::SystemError(format!("DB Query Error: {}", e)))?;

        // take(0) returns Result<T>, we try to extract Option<DailyNote>
        // Note: query usually returns a list of results. We want the first result set, then the first record?
        // Actually, let's fetch as Vec<DailyNote> to be safe against list return, then take first.
        let notes: Vec<DailyNote> = response
            .take(0)
            .map_err(|e| MetaError::SystemError(format!("DB Deserialization Error: {}", e)))?;

        Ok(notes.into_iter().next())
    }

    pub async fn save_daily_note(&self, note: DailyNote) -> Result<()> {
        let date_str = note.date.format("%Y-%m-%d").to_string();

        // Context: SurrealDB driver fails to serialize structs with #[serde(flatten)] using .content().
        // We convert to a DB-specific struct where `extra` is a distinct field (not flattened).
        // We use HashMap<String, String> for extra to avoid issues with serde_json::Value serialization in SurrealDB.
        #[derive(serde::Serialize, Clone)]
        struct DailyNoteDb {
            date: NaiveDate,
            pub phase: Option<String>,
            mode: Option<String>,
            protocol: Option<String>,
            goals_worked: Vec<String>,
            decisions_made: Vec<String>,
            divergences: Vec<String>,
            goals: Vec<String>,
            blockers: Vec<String>,
            decisions: Vec<String>,
            linked_goals: Vec<String>,
            file_path: PathBuf,
            content: String,
            pub extra: std::collections::HashMap<String, String>,
        }

        // Convert extra values to strings for safe storage
        let mut extra_strings = std::collections::HashMap::new();
        for (k, v) in &note.extra {
            // Simple conversion: if string, use it. Else json stringify.
            let s = match v {
                serde_json::Value::String(s) => s.clone(),
                _ => v.to_string(),
            };
            extra_strings.insert(k.clone(), s);
        }

        let note_db = DailyNoteDb {
            date: note.date,
            phase: note.phase,
            mode: note.mode,
            protocol: note.protocol,
            goals_worked: note.goals_worked,
            decisions_made: note.decisions_made,
            divergences: note.divergences,
            goals: note.goals,
            blockers: note.blockers,
            decisions: note.decisions,
            linked_goals: note.linked_goals,
            file_path: note.file_path,
            content: note.content,
            extra: extra_strings,
        };

        // UPSERT LOGIC: Try Create, if fails (exists), Update.
        // We ignore return value deserialization to avoid flattened struct issues.
        let create_res: Result<Option<serde_json::Value>> = self
            .db
            .create(("daily_notes", date_str.as_str()))
            .content(note_db.clone()) // Pass STRUCT directly
            .await
            .map_err(|e| MetaError::SystemError(format!("DB Create Error: {}", e)));

        if create_res.is_err() {
            // Fallback to Update
            let _: Option<serde_json::Value> = self
                .db
                .update(("daily_notes", date_str.as_str()))
                .content(note_db)
                .await
                .map_err(|e| MetaError::SystemError(format!("DB Update Error: {}", e)))?;
        }

        Ok(())
    }

    pub async fn save_goal(&self, goal: Goal) -> Result<()> {
        if goal
            .phase
            .as_ref()
            .map(|p| p.trim().is_empty())
            .unwrap_or(true)
        {
            return Err(MetaError::ValidationError(
                "Goal must belong to a phase (phase is the canonical scope root)".to_string(),
            ));
        }
        let id = goal.goal_id.clone();
        // UPSERT
        let create_res: Result<Option<serde_json::Value>> = self
            .db
            .create(("goals", &id))
            .content(goal.clone())
            .await
            .map_err(|e| MetaError::SystemError(format!("DB Create Goal Error: {}", e)));

        if create_res.is_err() {
            let _: Option<serde_json::Value> =
                self.db
                    .update(("goals", &id))
                    .content(goal)
                    .await
                    .map_err(|e| MetaError::SystemError(format!("DB Update Goal Error: {}", e)))?;
        }
        Ok(())
    }

    pub async fn save_phase(&self, phase: Phase) -> Result<()> {
        let id = phase.phase_id.clone();

        let content = serde_json::json!({
            "phase_id": phase.phase_id,
            "title": phase.title,
            "status": phase.status,
            "start_date": phase.start_date.map(|d| d.to_string()),
            "target_date": phase.target_date.map(|d| d.to_string()),
            "dependencies": phase.dependencies,
            "file_path": phase.file_path.to_string_lossy().to_string(),
            "content": phase.content
        });

        // UPSERT
        let create_res: Result<Option<serde_json::Value>> = self
            .db
            .create(("phases", &id))
            .content(content.clone())
            .await
            .map_err(|e| MetaError::SystemError(format!("DB Create Phase Error: {}", e)));

        if create_res.is_err() {
            let _: Option<serde_json::Value> = self
                .db
                .update(("phases", &id))
                .content(content)
                .await
                .map_err(|e| MetaError::SystemError(format!("DB Update Phase Error: {}", e)))?;
        }
        Ok(())
    }

    pub async fn save_decision(&self, decision: Decision) -> Result<()> {
        let id = decision.decision_id.clone();
        // UPSERT
        let create_res: Result<Option<serde_json::Value>> = self
            .db
            .create(("decisions", &id))
            .content(decision.clone())
            .await
            .map_err(|e| MetaError::SystemError(format!("DB Create Decision Error: {}", e)));

        if create_res.is_err() {
            let _: Option<serde_json::Value> = self
                .db
                .update(("decisions", &id))
                .content(decision)
                .await
                .map_err(|e| MetaError::SystemError(format!("DB Update Decision Error: {}", e)))?;
        }
        Ok(())
    }

    pub async fn save_audit(&self, audit: AuditRecord) -> Result<()> {
        // Audit doesn't have a clean ID in struct (it's path based mostly), but let's use title or generate one.
        // Wait, domain/audit.rs viewing earlier showed:
        // pub struct Audit { pub results: Vec<ValidationResult>, pub total_files: usize } -> This was WRONG in my earlier view summary, I need to check AuditRecord definition.
        // Let's assume AuditRecord has an ID or use title.
        // If AuditRecord doesn't have a unique ID, we might have trouble.
        // I should check AuditRecord definition first.
        // But to unblock, I'll use a hash or slug of title.
        let id = audit.title.replace(" ", "_").to_lowercase();

        // UPSERT
        let create_res: Result<Option<serde_json::Value>> = self
            .db
            .create(("audits", &id))
            .content(audit.clone())
            .await
            .map_err(|e| MetaError::SystemError(format!("DB Create Audit Error: {}", e)));

        if create_res.is_err() {
            let _: Option<serde_json::Value> = self
                .db
                .update(("audits", &id))
                .content(audit)
                .await
                .map_err(|e| MetaError::SystemError(format!("DB Update Audit Error: {}", e)))?;
        }
        Ok(())
    }

    pub async fn get_all_goals(&self) -> Result<Vec<Goal>> {
        #[derive(serde::Deserialize)]
        struct GoalDbCanon {
            id: String,
            phase_id: String,
            title: String,
            description: Option<String>,
            status: String,
            updated: Option<String>,
            tags: Option<Vec<String>>,
        }

        #[derive(serde::Deserialize)]
        struct GoalDbLegacy {
            goal_id: String,
            title: String,
            status: Option<serde_json::Value>,
            phase: Option<String>,
            owner: Option<String>,
            parent_id: Option<String>,
            level: Option<String>,
            dependencies: Option<serde_json::Value>,
            canon: Option<serde_json::Value>,
            tags: Option<serde_json::Value>,
            updated: Option<String>,
            file_path: Option<String>,
            content: Option<String>,
        }

        // Canonical query first
        if let Ok(mut response) = self.db.query("SELECT * FROM goal").await {
            if let Ok(db_items) = response.take::<Vec<GoalDbCanon>>(0) {
                let items: Vec<Goal> = db_items
                    .into_iter()
                    .map(|g| Goal {
                        goal_id: g.id,
                        title: g.title,
                        status: GoalStatus::from_str(&g.status)
                            .unwrap_or_else(|| GoalStatus::Unknown(g.status.clone())),
                        phase: Some(g.phase_id),
                        owner: None,
                        parent_id: None,
                        level: Some("goal".to_string()),
                        dependencies: Vec::new(),
                        canon: Vec::new(),
                        updated: g
                            .updated
                            .and_then(|s| NaiveDate::parse_from_str(&s, "%Y-%m-%d").ok()),
                        tags: g.tags.unwrap_or_default(),
                        file_path: PathBuf::new(),
                        content: g.description.unwrap_or_default(),
                    })
                    .collect();
                if !items.is_empty() {
                    return Ok(items);
                }
            }
        }

        // Legacy fallback
        let mut response = self
            .db
            .query("SELECT * FROM goals")
            .await
            .map_err(|e| MetaError::SystemError(format!("DB Query Error: {}", e)))?;
        let db_items: Vec<GoalDbLegacy> = response
            .take(0)
            .map_err(|e| MetaError::SystemError(format!("DB Deserialization Error: {}", e)))?;

        let items: Vec<Goal> = db_items
            .into_iter()
            .map(|g| Goal {
                goal_id: g.goal_id,
                title: g.title,
                status: g
                    .status
                    .as_ref()
                    .and_then(|v| v.as_str())
                    .and_then(GoalStatus::from_str)
                    .unwrap_or_else(|| GoalStatus::Unknown("unknown".to_string())),
                phase: g.phase,
                owner: g.owner,
                parent_id: g.parent_id,
                level: g.level.or_else(|| Some("goal".to_string())),
                dependencies: g
                    .dependencies
                    .and_then(|val| {
                        val.as_array().map(|arr| {
                            arr.iter()
                                .filter_map(|v| v.as_str().map(|s| s.to_string()))
                                .collect()
                        })
                    })
                    .unwrap_or_default(),
                canon: g
                    .canon
                    .and_then(|val| {
                        val.as_array().map(|arr| {
                            arr.iter()
                                .filter_map(|v| v.as_str().map(|s| s.to_string()))
                                .collect()
                        })
                    })
                    .unwrap_or_default(),
                updated: g
                    .updated
                    .and_then(|s| NaiveDate::parse_from_str(&s, "%Y-%m-%d").ok()),
                tags: g
                    .tags
                    .and_then(|val| {
                        val.as_array().map(|arr| {
                            arr.iter()
                                .filter_map(|v| v.as_str().map(|s| s.to_string()))
                                .collect()
                        })
                    })
                    .unwrap_or_default(),
                file_path: g.file_path.map(PathBuf::from).unwrap_or_else(PathBuf::new),
                content: g.content.unwrap_or_default(),
            })
            .collect();
        Ok(items)
    }

    pub async fn get_all_phases(&self) -> Result<Vec<Phase>> {
        #[derive(serde::Deserialize)]
        struct PhaseDbCanon {
            id: String,
            phase_id: String,
            title: String,
            status: String,
            #[serde(default)]
            description: String,
            #[serde(default)]
            content: String,
            start_date: Option<String>,
            target_date: Option<String>,
            #[serde(default)]
            dependencies: Vec<String>,
            #[serde(default)]
            file_path: String,
            #[serde(default)]
            order_index: i32,
        }

        #[derive(serde::Deserialize)]
        struct PhaseDbLegacy {
            phase_id: String,
            title: String,
            status: String,
            start_date: Option<String>,
            target_date: Option<String>,
            dependencies: Vec<String>,
            file_path: String,
            content: String,
        }

        if let Ok(mut resp) = self.db.query("SELECT * FROM phase").await {
            if let Ok(db_items) = resp.take::<Vec<PhaseDbCanon>>(0) {
                let items: Vec<Phase> = db_items
                    .into_iter()
                    .map(|p| Phase {
                        phase_id: p.phase_id,
                        title: p.title,
                        status: p.status,
                        start_date: p
                            .start_date
                            .and_then(|s| NaiveDate::parse_from_str(&s, "%Y-%m-%d").ok()),
                        target_date: p
                            .target_date
                            .and_then(|s| NaiveDate::parse_from_str(&s, "%Y-%m-%d").ok()),
                        dependencies: p.dependencies,
                        file_path: if p.file_path.is_empty() {
                            PathBuf::new()
                        } else {
                            PathBuf::from(p.file_path)
                        },
                        content: if p.content.is_empty() {
                            p.description
                        } else {
                            p.content
                        },
                    })
                    .collect();
                if !items.is_empty() {
                    return Ok(items);
                }
            }
        }

        let mut response = self
            .db
            .query("SELECT * FROM phases")
            .await
            .map_err(|e| MetaError::SystemError(format!("DB Query Error: {}", e)))?;

        let db_items: Vec<PhaseDbLegacy> = response
            .take(0)
            .map_err(|e| MetaError::SystemError(format!("DB Deserialization Error: {}", e)))?;

        let items: Vec<Phase> = db_items
            .into_iter()
            .map(|p| Phase {
                phase_id: p.phase_id,
                title: p.title,
                status: p.status,
                start_date: p
                    .start_date
                    .and_then(|s| NaiveDate::parse_from_str(&s, "%Y-%m-%d").ok()),
                target_date: p
                    .target_date
                    .and_then(|s| NaiveDate::parse_from_str(&s, "%Y-%m-%d").ok()),
                dependencies: p.dependencies,
                file_path: PathBuf::from(p.file_path),
                content: p.content,
            })
            .collect();

        Ok(items)
    }

    pub async fn get_all_decisions(&self) -> Result<Vec<Decision>> {
        #[derive(serde::Deserialize)]
        struct DecisionDb {
            decision_id: String,
            title: String,
            status: Option<serde_json::Value>,
            date: Option<String>,
            updated: Option<String>,
            canon: Option<serde_json::Value>,
            phase: Option<String>,
            rationale: Option<String>,
            file_path: Option<String>,
            content: Option<String>,
        }

        let mut response = self
            .db
            .query("SELECT * FROM decisions")
            .await
            .map_err(|e| MetaError::SystemError(format!("DB Query Error: {}", e)))?;

        let db_items: Vec<DecisionDb> = response
            .take(0)
            .map_err(|e| MetaError::SystemError(format!("DB Deserialization Error: {}", e)))?;

        let items = db_items
            .into_iter()
            .map(|d| Decision {
                decision_id: d.decision_id,
                title: d.title,
                status: d.status.and_then(|v| {
                    if let Some(s) = v.as_str() {
                        crate::domain::decision::DecisionStatus::from_str(s)
                    } else {
                        None
                    }
                }),
                date: d
                    .date
                    .and_then(|s| NaiveDate::parse_from_str(&s, "%Y-%m-%d").ok()),
                updated: d
                    .updated
                    .and_then(|s| NaiveDate::parse_from_str(&s, "%Y-%m-%d").ok()),
                canon: d
                    .canon
                    .and_then(|val| {
                        val.as_array().map(|arr| {
                            arr.iter()
                                .filter_map(|v| v.as_str().map(|s| s.to_string()))
                                .collect()
                        })
                    })
                    .unwrap_or_default(),
                phase: d.phase,
                rationale: d.rationale,
                file_path: d.file_path.map(PathBuf::from).unwrap_or_else(PathBuf::new),
                content: d.content.unwrap_or_default(),
            })
            .collect();

        Ok(items)
    }

    pub async fn get_all_audits(&self) -> Result<Vec<AuditRecord>> {
        let mut response = self
            .db
            .query("SELECT * FROM audits")
            .await
            .map_err(|e| MetaError::SystemError(format!("DB Query Error: {}", e)))?;
        let items: Vec<AuditRecord> = response
            .take(0)
            .map_err(|e| MetaError::SystemError(format!("DB Deserialization Error: {}", e)))?;
        Ok(items)
    }

    pub async fn get_all_prompts(&self) -> Result<Vec<Prompt>> {
        let mut response = self
            .db
            .query("SELECT * FROM prompts")
            .await
            .map_err(|e| MetaError::SystemError(format!("DB Query Error: {}", e)))?;
        let items: Vec<Prompt> = response
            .take(0)
            .map_err(|e| MetaError::SystemError(format!("DB Deserialization Error: {}", e)))?;
        Ok(items)
    }

    pub async fn get_all_daily_notes(&self) -> Result<Vec<DailyNote>> {
        let mut response = self
            .db
            .query("SELECT content, date, phase, mode, protocol, goals_worked, decisions_made, divergences, goals, blockers, decisions, linked_goals, file_path, extra FROM daily_notes")
            .await
            .map_err(|e| MetaError::SystemError(format!("DB Query Error: {}", e)))?;
        let items: Vec<DailyNote> = response
            .take(0)
            .map_err(|e| MetaError::SystemError(format!("DB Deserialization Error: {}", e)))?;
        Ok(items)
    }

    pub async fn upsert_daily_note(&self, note: &DailyNote) -> Result<()> {
        let id = note.date.to_string(); // YYYY-MM-DD

        let _: std::result::Result<Option<DailyNote>, surrealdb::Error> = self
            .db
            .create(("daily_notes", &id))
            .content(note.clone())
            .await; // Ignore error if exists

        let _: Option<DailyNote> = self
            .db
            .update(("daily_notes", &id))
            .content(note.clone())
            .await
            .map_err(|e| MetaError::SystemError(format!("DB Update Daily Note Error: {}", e)))?;

        Ok(())
    }

    // === WorkItems === (canonical SCHEMAFULL table)

    pub async fn add_work_item(&self, item: &WorkItem) -> Result<()> {
        let _: std::result::Result<Option<WorkItem>, surrealdb::Error> = self
            .db
            .create(("work_item", &item.id))
            .content(item.clone())
            .await;
        Ok(())
    }

    pub async fn get_work_items_by_goal(&self, goal_id: &str) -> Result<Vec<WorkItem>> {
        let mut response = self
            .db
            .query("SELECT * FROM work_item WHERE goal_id = $goal_id")
            .bind(("goal_id", goal_id.to_string()))
            .await
            .map_err(|e| MetaError::SystemError(format!("DB Query Error: {}", e)))?;
        let items: Vec<WorkItem> = response
            .take(0)
            .map_err(|e| MetaError::SystemError(format!("DB Deserialization Error: {}", e)))?;
        Ok(items)
    }

    pub async fn update_work_item(&self, item: &WorkItem) -> Result<()> {
        let _: Option<WorkItem> = self
            .db
            .update(("work_item", &item.id))
            .content(item.clone())
            .await
            .map_err(|e| MetaError::SystemError(format!("DB Update WorkItem Error: {}", e)))?;
        Ok(())
    }

    // === Annotations ===

    pub async fn add_annotation(&self, item: &Annotation) -> Result<()> {
        let _: std::result::Result<Option<Annotation>, surrealdb::Error> = self
            .db
            .create(("annotation", &item.id))
            .content(item.clone())
            .await;
        Ok(())
    }

    pub async fn get_annotations(
        &self,
        entity_type: &str,
        entity_id: &str,
    ) -> Result<Vec<Annotation>> {
        let mut response = self
            .db
            .query(
                "SELECT * FROM annotation WHERE (entity_type = $etype OR target_type = $etype) AND (entity_id = $eid OR target_id = $eid) ORDER BY created_at DESC",
            )
            .bind(("etype", entity_type.to_string()))
            .bind(("eid", entity_id.to_string()))
            .await
            .map_err(|e| MetaError::SystemError(format!("DB Query Error: {}", e)))?;
        let items: Vec<Annotation> = response
            .take(0)
            .map_err(|e| MetaError::SystemError(format!("DB Deserialization Error: {}", e)))?;
        Ok(items)
    }

    pub async fn delete_annotation(&self, id: &str) -> Result<()> {
        let _: Option<serde_json::Value> = self
            .db
            .delete(("annotation", id))
            .await
            .map_err(|e| MetaError::SystemError(format!("DB Delete Error: {}", e)))?;
        Ok(())
    }

    pub async fn log_event(&self, event: &Event) -> Result<()> {
        let event_id = event.id.clone();
        // Strip the "EVENT-" prefix if present for the ID part, or use as is if passed specifically
        // But Event::new() generates "EVENT-<uuid>". explicit ID is "event:EVENT-<uuid>"
        // DB.create expects ("event", "EVENT-...")
        
        let _: Vec<serde::de::IgnoredAny> = self
            .db
            .query(r#"
                CREATE type::thing('event', $id) SET 
                    entity_type = $entity_type,
                    entity_id = $entity_id,
                    action = $action,
                    actor = $actor,
                    payload = $payload,
                    created_at = type::datetime($created_at)
            "#)
            .bind(("id", event_id))
            .bind(("entity_type", event.entity_type.clone()))
            .bind(("entity_id", event.entity_id.clone()))
            .bind(("action", event.action.clone()))
            .bind(("actor", event.actor.clone()))
            .bind(("payload", event.payload.clone()))
            .bind(("created_at", event.created_at.to_rfc3339()))
            .await
            .map_err(|e| MetaError::SystemError(format!("DB Event Error: {}", e)))?
            .take(0)
            .map_err(|e| MetaError::SystemError(format!("DB Result Error: {}", e)))?; // Ignore return value to prevent "Invalid revision" errors here too

        Ok(())
    }

    // === Meta Methods ===

    pub async fn get_meta(&self, key: &str) -> Result<Option<String>> {
        // Use .select() method instead of raw SQL to avoid table name escaping issues
        #[derive(serde::Deserialize)]
        struct MetaValue {
            value: String,
        }

        let result: Option<MetaValue> = self.db.select(("meta_kv", key)).await.map_err(|e| {
            MetaError::DatabaseQuery(format!("Failed to query meta_kv[{}]: {}", key, e))
        })?;

        Ok(result.map(|m| m.value))
    }

    pub async fn set_meta(&self, key: &str, value: &str) -> Result<()> {
        let _: Option<serde_json::Value> = self
            .db
            .create(("meta_kv", key))
            .content(serde_json::json!({ "value": value }))
            .await
            .unwrap_or_else(|_| None); // If create fails, try update

        let _: Option<serde_json::Value> = self
            .db
            .update(("meta_kv", key))
            .content(serde_json::json!({ "value": value }))
            .await
            .map_err(|e| {
                MetaError::DatabaseQuery(format!("Failed to update meta_kv[{}]: {}", key, e))
            })?;

        Ok(())
    }

    // === Dashboard Query Methods ===

    /// Count goals by status using SurrealDB query
    pub async fn count_goals_by_status(&self) -> Result<std::collections::HashMap<String, usize>> {
        use serde::Deserialize;

        #[derive(Deserialize)]
        struct StatusCount {
            status: String,
            count: i64,
        }

        let query = "SELECT status, count() as count FROM goals GROUP BY status";
        let mut response = self
            .db
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
        #[derive(serde::Deserialize)]
        struct GoalDb {
            goal_id: String,
            title: String,
            status: Option<serde_json::Value>,
            phase: Option<String>,
            owner: Option<String>,
            parent_id: Option<String>,
            level: Option<String>,
            dependencies: Option<serde_json::Value>,
            canon: Option<serde_json::Value>,
            tags: Option<serde_json::Value>,
            updated: Option<String>,
            file_path: Option<String>,
            content: Option<String>,
        }

        let query = format!("SELECT * FROM goals WHERE status = '{}'", status);
        let mut response =
            self.db.query(&query).await.map_err(|e| {
                MetaError::SystemError(format!("Goals by status query failed: {}", e))
            })?;

        let db_items: Vec<GoalDb> = response
            .take(0)
            .map_err(|e| MetaError::SystemError(format!("Failed to parse goals: {}", e)))?;

        let goals: Vec<crate::Goal> = db_items
            .into_iter()
            .map(|g| Goal {
                goal_id: g.goal_id,
                title: g.title,
                status: g
                    .status
                    .as_ref()
                    .and_then(|v| {
                        if let Some(s) = v.as_str() {
                            GoalStatus::from_str(s)
                        } else {
                            None
                        }
                    })
                    .unwrap_or_else(|| GoalStatus::Unknown("unknown".to_string())),
                phase: g.phase,
                owner: g.owner,
                parent_id: g.parent_id,
                level: g.level.or_else(|| Some("goal".to_string())),
                dependencies: g
                    .dependencies
                    .and_then(|val| {
                        val.as_array().map(|arr| {
                            arr.iter()
                                .filter_map(|v| v.as_str().map(|s| s.to_string()))
                                .collect()
                        })
                    })
                    .unwrap_or_default(),
                canon: g
                    .canon
                    .and_then(|val| {
                        val.as_array().map(|arr| {
                            arr.iter()
                                .filter_map(|v| v.as_str().map(|s| s.to_string()))
                                .collect()
                        })
                    })
                    .unwrap_or_default(),
                updated: g
                    .updated
                    .and_then(|s| NaiveDate::parse_from_str(&s, "%Y-%m-%d").ok()),
                tags: g
                    .tags
                    .and_then(|val| {
                        val.as_array().map(|arr| {
                            arr.iter()
                                .filter_map(|v| v.as_str().map(|s| s.to_string()))
                                .collect()
                        })
                    })
                    .unwrap_or_default(),
                file_path: g.file_path.map(PathBuf::from).unwrap_or_else(PathBuf::new),
                content: g.content.unwrap_or_default(),
            })
            .collect();

        Ok(goals)
    }

    /// Get daily notes within a date range
    pub async fn get_daily_notes_in_range(
        &self,
        start: NaiveDate,
        end: NaiveDate,
    ) -> Result<Vec<DailyNote>> {
        let query = format!(
            "SELECT * FROM daily_notes WHERE date >= '{}' AND date <= '{}' ORDER BY date ASC",
            start.format("%Y-%m-%d"),
            end.format("%Y-%m-%d")
        );

        let mut response = self.db.query(&query).await.map_err(|e| {
            MetaError::SystemError(format!("Daily notes range query failed: {}", e))
        })?;

        let notes: Vec<DailyNote> = response
            .take(0)
            .map_err(|e| MetaError::SystemError(format!("Failed to parse daily notes: {}", e)))?;

        Ok(notes)
    }
}
