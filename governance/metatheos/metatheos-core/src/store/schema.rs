use crate::errors::Result;
use surrealdb::engine::local::Db;
use surrealdb::Surreal;

/// Initialize the complete DB-first schema for Metatheos
///
/// This implements the canonical schema with:
/// - Phases as the structural spine
/// - Goals as immutable commitments within phases
/// - Work items as the execution layer (goal/subgoal/task hierarchy)
/// - Days as the daily reality layer
/// - Annotations for universal note-taking
/// - Events for audit trail
/// - AI runs for draft gating
pub async fn initialize_schema(db: &Surreal<Db>) -> Result<()> {
    // 1. CORE STRUCTURAL SPINE

    // 1.1 Phase table - Fixed scopes of meaning
    let _ = db.query("DEFINE TABLE phase SCHEMAFULL").await;
    let _ = db
        .query("DEFINE FIELD id ON TABLE phase TYPE string ASSERT $value != NONE")
        .await;
    let _ = db
        .query("DEFINE FIELD phase_id ON TABLE phase TYPE string ASSERT $value != NONE")
        .await;
    let _ = db
        .query("DEFINE FIELD title ON TABLE phase TYPE string ASSERT $value != NONE")
        .await;
    let _ = db
        .query("DEFINE FIELD description ON TABLE phase TYPE string DEFAULT ''")
        .await;
    let _ = db
        .query("DEFINE FIELD content ON TABLE phase TYPE string DEFAULT ''")
        .await;
    let _ = db.query("DEFINE FIELD status ON TABLE phase TYPE string ASSERT $value IN ['planned', 'active', 'closed', 'archived']").await;
    let _ = db
        .query("DEFINE FIELD start_date ON TABLE phase TYPE option<string>")
        .await;
    let _ = db
        .query("DEFINE FIELD target_date ON TABLE phase TYPE option<string>")
        .await;
    let _ = db
        .query("DEFINE FIELD dependencies ON TABLE phase TYPE array<string> DEFAULT []")
        .await;
    let _ = db
        .query("DEFINE FIELD file_path ON TABLE phase TYPE string DEFAULT ''")
        .await;
    let _ = db
        .query("DEFINE FIELD order_index ON TABLE phase TYPE int DEFAULT 0")
        .await;
    let _ = db
        .query("DEFINE FIELD created_at ON TABLE phase TYPE datetime DEFAULT time::now()")
        .await;
    let _ = db
        .query("DEFINE FIELD closed_at ON TABLE phase TYPE option<datetime>")
        .await;
    let _ = db
        .query("DEFINE INDEX phase_id_idx ON TABLE phase COLUMNS phase_id UNIQUE")
        .await;

    // 1.2 Goal table - Commitments within a phase
    let _ = db.query("DEFINE TABLE goal SCHEMAFULL").await;
    let _ = db
        .query("DEFINE FIELD id ON TABLE goal TYPE string ASSERT $value != NONE")
        .await;
    let _ = db
        .query("DEFINE FIELD phase_id ON TABLE goal TYPE string ASSERT $value != NONE")
        .await;
    let _ = db
        .query("DEFINE FIELD title ON TABLE goal TYPE string ASSERT $value != NONE")
        .await;
    let _ = db
        .query("DEFINE FIELD description ON TABLE goal TYPE string DEFAULT ''")
        .await;
    // Allow all GoalStatus variants including unknown statuses
    let _ = db.query("DEFINE FIELD status ON TABLE goal TYPE string ASSERT $value != NONE").await;
    let _ = db.query("DEFINE FIELD priority ON TABLE goal TYPE string ASSERT $value IN ['low', 'normal', 'high', 'critical'] DEFAULT 'normal'").await;
    let _ = db
        .query("DEFINE FIELD owner ON TABLE goal TYPE option<string>")
        .await;
    let _ = db
        .query("DEFINE FIELD dependencies ON TABLE goal TYPE array<string> DEFAULT []")
        .await;
    let _ = db
        .query("DEFINE FIELD tags ON TABLE goal TYPE array<string> DEFAULT []")
        .await;
    let _ = db
        .query("DEFINE FIELD updated ON TABLE goal TYPE option<string>")
        .await;
    let _ = db
        .query("DEFINE FIELD created_at ON TABLE goal TYPE datetime DEFAULT time::now()")
        .await;
    let _ = db
        .query("DEFINE FIELD closed_at ON TABLE goal TYPE option<datetime>")
        .await;
    let _ = db
        .query("DEFINE INDEX goal_id_idx ON TABLE goal COLUMNS id UNIQUE")
        .await;
    let _ = db
        .query("DEFINE INDEX goal_phase_idx ON TABLE goal COLUMNS phase_id")
        .await;

    // 2. EXECUTION LAYER

    // 2.1 Work Item table - Unified hierarchy (goal/subgoal/task)
    let _ = db.query("DEFINE TABLE work_item SCHEMAFULL").await;
    let _ = db
        .query("DEFINE FIELD id ON TABLE work_item TYPE string ASSERT $value != NONE")
        .await;
    let _ = db
        .query("DEFINE FIELD goal_id ON TABLE work_item TYPE string ASSERT $value != NONE")
        .await;
    let _ = db
        .query("DEFINE FIELD parent_id ON TABLE work_item TYPE option<string>")
        .await;
    let _ = db.query("DEFINE FIELD level ON TABLE work_item TYPE string ASSERT $value IN ['goal', 'subgoal', 'task']").await;
    let _ = db
        .query("DEFINE FIELD title ON TABLE work_item TYPE string ASSERT $value != NONE")
        .await;
    let _ = db
        .query("DEFINE FIELD description ON TABLE work_item TYPE string DEFAULT ''")
        .await;
    let _ = db.query("DEFINE FIELD status ON TABLE work_item TYPE string ASSERT $value IN ['open', 'active', 'blocked', 'done']").await;
    let _ = db
        .query("DEFINE FIELD order_index ON TABLE work_item TYPE int DEFAULT 0")
        .await;
    let _ = db
        .query("DEFINE FIELD created_at ON TABLE work_item TYPE datetime DEFAULT time::now()")
        .await;
    let _ = db
        .query("DEFINE FIELD completed_at ON TABLE work_item TYPE option<datetime>")
        .await;
    let _ = db
        .query("DEFINE INDEX work_item_id_idx ON TABLE work_item COLUMNS id UNIQUE")
        .await;
    let _ = db
        .query("DEFINE INDEX work_item_goal_idx ON TABLE work_item COLUMNS goal_id")
        .await;
    let _ = db
        .query("DEFINE INDEX work_item_parent_idx ON TABLE work_item COLUMNS parent_id")
        .await;

    // 3. DAILY REALITY LAYER

    // 3.1 Day table - Single calendar day
    let _ = db.query("DEFINE TABLE day SCHEMAFULL").await;
    let _ = db
        .query("DEFINE FIELD id ON TABLE day TYPE string ASSERT $value != NONE")
        .await; // Format: "YYYY-MM-DD"
    let _ = db
        .query("DEFINE FIELD phase_id ON TABLE day TYPE string ASSERT $value != NONE")
        .await;
    let _ = db.query("DEFINE FIELD day_type ON TABLE day TYPE string ASSERT $value IN ['light', 'heavy', 'review', 'rest']").await;
    let _ = db
        .query("DEFINE FIELD created_at ON TABLE day TYPE datetime DEFAULT time::now()")
        .await;
    let _ = db
        .query("DEFINE INDEX day_id_idx ON TABLE day COLUMNS id UNIQUE")
        .await;
    let _ = db
        .query("DEFINE INDEX day_phase_idx ON TABLE day COLUMNS phase_id")
        .await;

    // 3.2 Day Goal table - Links between days and goals
    let _ = db.query("DEFINE TABLE day_goal SCHEMAFULL").await;
    let _ = db
        .query("DEFINE FIELD day_id ON TABLE day_goal TYPE string ASSERT $value != NONE")
        .await;
    let _ = db
        .query("DEFINE FIELD goal_id ON TABLE day_goal TYPE string ASSERT $value != NONE")
        .await;
    let _ = db
        .query("DEFINE FIELD required ON TABLE day_goal TYPE bool DEFAULT false")
        .await;
    let _ = db
        .query(
            "DEFINE INDEX day_goal_composite_idx ON TABLE day_goal COLUMNS day_id, goal_id UNIQUE",
        )
        .await;

    // 3.3 Day Log table - Daily notes and narrative
    let _ = db.query("DEFINE TABLE day_log SCHEMAFULL").await;
    let _ = db
        .query("DEFINE FIELD id ON TABLE day_log TYPE string ASSERT $value != NONE")
        .await;
    let _ = db
        .query("DEFINE FIELD day_id ON TABLE day_log TYPE string ASSERT $value != NONE")
        .await;
    let _ = db
        .query("DEFINE FIELD content ON TABLE day_log TYPE string ASSERT $value != NONE")
        .await;
    let _ = db
        .query("DEFINE FIELD created_at ON TABLE day_log TYPE datetime DEFAULT time::now()")
        .await;
    let _ = db
        .query("DEFINE INDEX day_log_day_idx ON TABLE day_log COLUMNS day_id")
        .await;

    // 4. ANNOTATION SYSTEM

    // 4.1 Annotation table - Universal notes/evidence
    let _ = db.query("DEFINE TABLE annotation SCHEMAFULL").await;
    let _ = db
        .query("DEFINE FIELD id ON TABLE annotation TYPE string ASSERT $value != NONE")
        .await;
    let _ = db.query("DEFINE FIELD entity_type ON TABLE annotation TYPE string ASSERT $value IN ['phase', 'goal', 'work_item', 'day', 'day_log', 'event', 'ai_run']").await;
    let _ = db
        .query("DEFINE FIELD entity_id ON TABLE annotation TYPE string ASSERT $value != NONE")
        .await;
    let _ = db
        .query("DEFINE FIELD content ON TABLE annotation TYPE string ASSERT $value != NONE")
        .await;
    let _ = db.query("DEFINE FIELD author_type ON TABLE annotation TYPE string ASSERT $value IN ['user', 'ai']").await;
    let _ = db
        .query("DEFINE FIELD author_ref ON TABLE annotation TYPE option<string>")
        .await; // ai_run.id if AI
    let _ = db
        .query("DEFINE FIELD created_at ON TABLE annotation TYPE datetime DEFAULT time::now()")
        .await;
    let _ = db
        .query(
            "DEFINE INDEX annotation_entity_idx ON TABLE annotation COLUMNS entity_type, entity_id",
        )
        .await;

    // 5. EVENT & AUDIT LAYER

    // 5.1 Event table - Audit trail for all mutations
    let _ = db.query("DEFINE TABLE event SCHEMAFULL").await;
    let _ = db
        .query("DEFINE FIELD id ON TABLE event TYPE string ASSERT $value != NONE")
        .await;
    let _ = db
        .query("DEFINE FIELD entity_type ON TABLE event TYPE string ASSERT $value != NONE")
        .await;
    let _ = db
        .query("DEFINE FIELD entity_id ON TABLE event TYPE string ASSERT $value != NONE")
        .await;
    let _ = db.query("DEFINE FIELD action ON TABLE event TYPE string ASSERT $value IN ['create', 'update', 'complete', 'reopen', 'link', 'delete']").await;
    let _ = db
        .query("DEFINE FIELD actor ON TABLE event TYPE string DEFAULT 'user'")
        .await; // 'user' or 'system' or 'ai'
    let _ = db
        .query("DEFINE FIELD payload ON TABLE event TYPE object")
        .await; // JSON object with change details
    let _ = db
        .query("DEFINE FIELD created_at ON TABLE event TYPE datetime DEFAULT time::now()")
        .await;
    let _ = db
        .query("DEFINE INDEX event_entity_idx ON TABLE event COLUMNS entity_type, entity_id")
        .await;
    let _ = db
        .query("DEFINE INDEX event_timestamp_idx ON TABLE event COLUMNS created_at")
        .await;

    // 6. AI LAYER

    // 6.1 Prompt Template table - Reusable prompts
    let _ = db.query("DEFINE TABLE prompt_template SCHEMAFULL").await;
    let _ = db
        .query("DEFINE FIELD id ON TABLE prompt_template TYPE string ASSERT $value != NONE")
        .await;
    let _ = db
        .query("DEFINE FIELD name ON TABLE prompt_template TYPE string ASSERT $value != NONE")
        .await;
    let _ = db.query("DEFINE FIELD intent ON TABLE prompt_template TYPE string ASSERT $value IN ['summarize', 'expand', 'critique', 'plan', 'refine', 'validate']").await;
    let _ = db
        .query("DEFINE FIELD template ON TABLE prompt_template TYPE string ASSERT $value != NONE")
        .await;
    let _ = db
        .query("DEFINE FIELD output_schema ON TABLE prompt_template TYPE option<object>")
        .await; // JSON schema for expected output
    let _ = db
        .query("DEFINE FIELD created_at ON TABLE prompt_template TYPE datetime DEFAULT time::now()")
        .await;
    let _ = db
        .query("DEFINE INDEX prompt_template_name_idx ON TABLE prompt_template COLUMNS name UNIQUE")
        .await;

    // 6.2 AI Run table - Every AI interaction logged
    let _ = db.query("DEFINE TABLE ai_run SCHEMAFULL").await;
    let _ = db
        .query("DEFINE FIELD id ON TABLE ai_run TYPE string ASSERT $value != NONE")
        .await;
    let _ = db.query("DEFINE FIELD provider ON TABLE ai_run TYPE string ASSERT $value IN ['ollama', 'openai', 'anthropic', 'mistral']").await;
    let _ = db
        .query("DEFINE FIELD model ON TABLE ai_run TYPE string ASSERT $value != NONE")
        .await;
    let _ = db.query("DEFINE FIELD intent ON TABLE ai_run TYPE string ASSERT $value IN ['summarize', 'expand', 'critique', 'plan', 'refine', 'validate', 'chat']").await;
    let _ = db
        .query("DEFINE FIELD context_ref ON TABLE ai_run TYPE object")
        .await; // JSON with phase_id, goal_id, work_item_id, etc.
    let _ = db
        .query("DEFINE FIELD prompt ON TABLE ai_run TYPE string ASSERT $value != NONE")
        .await;
    let _ = db
        .query("DEFINE FIELD response ON TABLE ai_run TYPE string ASSERT $value != NONE")
        .await;
    let _ = db.query("DEFINE FIELD status ON TABLE ai_run TYPE string ASSERT $value IN ['draft', 'applied', 'rejected'] DEFAULT 'draft'").await;
    let _ = db
        .query("DEFINE FIELD created_at ON TABLE ai_run TYPE datetime DEFAULT time::now()")
        .await;
    let _ = db
        .query("DEFINE INDEX ai_run_timestamp_idx ON TABLE ai_run COLUMNS created_at")
        .await;

    // 7. META & SYSTEM CONTROL

    // 7.1 Meta KV table - System configuration (key-value store)
    // Note: Using 'meta_kv' instead of 'meta' because 'meta' is a reserved keyword in SurrealDB
    let _ = db.query("DEFINE TABLE meta_kv SCHEMAFULL").await;
    let _ = db
        .query("DEFINE FIELD key ON TABLE meta_kv TYPE string ASSERT $value != NONE")
        .await;
    let _ = db
        .query("DEFINE FIELD value ON TABLE meta_kv TYPE option<string>")
        .await; // JSON string or simple value
    let _ = db
        .query("DEFINE INDEX meta_kv_key_idx ON TABLE meta_kv COLUMNS key UNIQUE")
        .await;

    // 8. LEGACY TABLES (Keep for backward compatibility during migration)

    // Keep daily_notes, goals, phases, decisions, audits, prompts as SCHEMALESS
    // These will be gradually migrated to the new schema
    let _ = db.query("DEFINE TABLE daily_notes SCHEMALESS").await;
    let _ = db.query("DEFINE TABLE goals SCHEMALESS").await;
    let _ = db.query("DEFINE TABLE phases SCHEMALESS").await;
    let _ = db.query("DEFINE TABLE decisions SCHEMALESS").await;
    let _ = db.query("DEFINE TABLE audits SCHEMALESS").await;
    let _ = db.query("DEFINE TABLE prompts SCHEMALESS").await;

    Ok(())
}
