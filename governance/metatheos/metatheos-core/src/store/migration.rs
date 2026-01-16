use crate::errors::Result;
use crate::store::SurrealStore;
use serde::Deserialize;
use std::path::Path;

const TARGET_SCHEMA_VERSION: u32 = 1;
const META_SCHEMA_KEY: &str = "schema_version";

#[derive(Debug, Deserialize)]
#[allow(dead_code)]
struct LegacyPhase {
    phase_id: String,
    title: String,
    status: String,
    start_date: Option<String>,
    target_date: Option<String>,
    dependencies: Vec<String>,
    content: String,
}

#[derive(Debug, Deserialize)]
#[allow(dead_code)]
struct LegacyGoal {
    goal_id: String,
    title: String,
    status: Option<serde_json::Value>,
    phase: Option<String>,
    owner: Option<String>,
    parent_id: Option<String>,
    level: Option<String>,
    dependencies: Option<serde_json::Value>,
    tags: Option<serde_json::Value>,
    content: Option<String>,
}

async fn current_schema_version(store: &SurrealStore) -> Result<u32> {
    if let Some(ver) = store.get_meta(META_SCHEMA_KEY).await? {
        return Ok(ver.parse::<u32>().unwrap_or(0));
    }
    Ok(0)
}

async fn set_schema_version(store: &SurrealStore, version: u32) -> Result<()> {
    store.set_meta(META_SCHEMA_KEY, &version.to_string()).await
}

fn map_phase_status(status: &str) -> String {
    let s = status.to_lowercase();
    if s.contains("active") {
        "active".to_string()
    } else if s.contains("closed") || s.contains("done") {
        "closed".to_string()
    } else if s.contains("archived") {
        "archived".to_string()
    } else {
        "planned".to_string()
    }
}

fn map_goal_status(status: &str) -> String {
    match status.to_lowercase().as_str() {
        "partial" => "partial".to_string(),
        "blocked" => "blocked".to_string(),
        "done" | "completed" | "archived" => "done".to_string(),
        _ => "open".to_string(),
    }
}

fn parse_order_index(phase_id: &str) -> i32 {
    phase_id
        .trim_start_matches(|c: char| !c.is_ascii_digit())
        .parse::<i32>()
        .unwrap_or(0)
}

async fn migrate_legacy(store: &SurrealStore) -> Result<()> {
    // Phase migration: legacy `phases` -> canonical `phase`
    let mut legacy_phase_resp = store.db.query("SELECT * FROM phases").await.map_err(|e| {
        crate::errors::MetaError::SystemError(format!("Phase migration query failed: {}", e))
    })?;
    let legacy_phases: Vec<LegacyPhase> = legacy_phase_resp.take(0).map_err(|e| {
        crate::errors::MetaError::SystemError(format!("Phase migration decode failed: {}", e))
    })?;

    for p in legacy_phases {
        let id = p.phase_id.clone();
        let status = map_phase_status(&p.status);
        let order_index = parse_order_index(&p.phase_id);
        let payload = serde_json::json!({
            "id": id,
            "title": p.title,
            "description": p.content,
            "status": status,
            "order_index": order_index
        });

        let create_res: std::result::Result<Option<serde_json::Value>, surrealdb::Error> = store
            .db
            .create(("phase", id.as_str()))
            .content(payload.clone())
            .await;

        if create_res.is_err() {
            let _: Option<serde_json::Value> = store
                .db
                .update(("phase", id.as_str()))
                .content(payload)
                .await
                .map_err(|e| {
                    crate::errors::MetaError::SystemError(format!(
                        "Phase migration write failed: {}",
                        e
                    ))
                })?;
        }
    }

    // Goal migration: legacy `goals` -> canonical `goal`
    let mut legacy_goal_resp = store.db.query("SELECT * FROM goals").await.map_err(|e| {
        crate::errors::MetaError::SystemError(format!("Goal migration query failed: {}", e))
    })?;
    let legacy_goals: Vec<LegacyGoal> = legacy_goal_resp.take(0).map_err(|e| {
        crate::errors::MetaError::SystemError(format!("Goal migration decode failed: {}", e))
    })?;

    for g in legacy_goals {
        let id = g.goal_id.clone();
        let phase_id = g.phase.clone().unwrap_or_default();
        let status = g
            .status
            .as_ref()
            .and_then(|v| v.as_str())
            .map(map_goal_status)
            .unwrap_or_else(|| "open".to_string());
        let dependencies: Vec<String> = g
            .dependencies
            .and_then(|val| {
                val.as_array().map(|arr| {
                    arr.iter()
                        .filter_map(|v| v.as_str().map(|s| s.to_string()))
                        .collect()
                })
            })
            .unwrap_or_default();
        let tags: Vec<String> = g
            .tags
            .and_then(|val| {
                val.as_array().map(|arr| {
                    arr.iter()
                        .filter_map(|v| v.as_str().map(|s| s.to_string()))
                        .collect()
                })
            })
            .unwrap_or_default();

        let payload = serde_json::json!({
            "id": id,
            "phase_id": phase_id,
            "title": g.title,
            "description": g.content.unwrap_or_default(),
            "status": status,
            "priority": "normal",
            "owner": g.owner.unwrap_or_default(),
            "dependencies": dependencies,
            "tags": tags
        });

        let create_res: std::result::Result<Option<serde_json::Value>, surrealdb::Error> = store
            .db
            .create(("goal", id.as_str()))
            .content(payload.clone())
            .await;

        if create_res.is_err() {
            let _: Option<serde_json::Value> = store
                .db
                .update(("goal", id.as_str()))
                .content(payload)
                .await
                .map_err(|e| {
                    crate::errors::MetaError::SystemError(format!(
                        "Goal migration write failed: {}",
                        e
                    ))
                })?;
        }
    }

    Ok(())
}

/// Run all pending migrations. Idempotent.
pub async fn migrate_all(store: &SurrealStore, _root: &Path) -> Result<()> {
    let current = current_schema_version(store).await?;
    if current >= TARGET_SCHEMA_VERSION {
        println!("Migration: schema version {} already applied", current);
        return Ok(());
    }

    println!(
        "Migration: upgrading schema from version {} to {}",
        current, TARGET_SCHEMA_VERSION
    );

    migrate_legacy(store).await?;
    set_schema_version(store, TARGET_SCHEMA_VERSION).await?;

    println!(
        "Migration: schema version {} applied",
        TARGET_SCHEMA_VERSION
    );
    Ok(())
}
