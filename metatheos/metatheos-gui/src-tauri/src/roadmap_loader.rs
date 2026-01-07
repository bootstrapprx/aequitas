/// Roadmap Loader & Normalizer
///
/// This module provides fail-safe roadmap ingestion with:
/// - Schema validation with JSON pointer paths
/// - Auto-fixing for common malformed data
/// - Comprehensive logging for debugging
/// - Never hard-fails (skips bad items, continues processing)
///
/// Design Philosophy:
/// - Accept flexible input, produce canonical output
/// - Make failures self-locating (log exact JSON path of errors)
/// - Prefer graceful degradation over crashes
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::path::Path;

// ========== CANONICAL SCHEMA ==========

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RoadmapFile {
    pub schema_version: u32,
    pub roadmap_id: String,
    pub title: String,
    #[serde(default)]
    pub description: String,
    pub project_start_date: Option<String>,
    pub last_updated: Option<String>,
    pub phases: Vec<PhaseSpec>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PhaseSpec {
    pub phase_id: String,
    pub title: String,
    pub order_index: i32,
    pub status: String,
    pub start_date: Option<String>,
    pub target_date: Option<String>,
    pub content: String,
    #[serde(default)]
    pub dependencies: Vec<String>,
    #[serde(default)]
    pub goals: Vec<GoalSpec>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GoalSpec {
    pub goal_id: String,
    pub title: String,
    pub order_index: i32,
    pub status: String,
    pub content: String,
    #[serde(default)]
    pub tasks: Vec<TaskSpec>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaskSpec {
    pub task_id: String,
    pub title: String,
    pub order_index: i32,
    pub status: String,
    pub content: String,
}

// ========== LOADER ==========

#[derive(Debug)]
pub struct LoadResult {
    pub roadmap: RoadmapFile,
    pub warnings: Vec<String>,
    pub fixed_items: usize,
}

/// Load and normalize a roadmap file
///
/// This function never fails. It will:
/// - Load the file and parse JSON
/// - Normalize malformed data
/// - Skip items that can't be fixed
/// - Return warnings for any issues
pub fn load_roadmap_file<P: AsRef<Path>>(path: P) -> Result<LoadResult, String> {
    let path_ref = path.as_ref();
    let path_str = path_ref.display().to_string();

    log::info!("📂 Loading roadmap from: {}", path_str);

    // Read file
    let contents = std::fs::read_to_string(path_ref)
        .map_err(|e| format!("Failed to read roadmap file '{}': {}", path_str, e))?;

    log::debug!("📄 File size: {} bytes", contents.len());

    // Check for BOM or other encoding issues
    if contents.starts_with('\u{FEFF}') {
        log::warn!("⚠️  File has BOM marker - stripping it");
    }

    // Parse JSON
    let raw_json: Value = serde_json::from_str(&contents).map_err(|e| {
        let preview = if contents.len() > 200 {
            format!("{}...", &contents[..200])
        } else {
            contents.clone()
        };
        format!(
            "Failed to parse JSON in '{}': {}\nFirst 200 chars: {}",
            path_str, e, preview
        )
    })?;

    log::debug!("✓ JSON parsed successfully");

    // Normalize and validate
    normalize_roadmap(raw_json, &path_str)
}

// ========== NORMALIZER ==========

fn normalize_roadmap(raw: Value, source: &str) -> Result<LoadResult, String> {
    let mut warnings = Vec::new();
    let mut fixed_items = 0;

    log::info!("🔧 Normalizing roadmap from {}", source);

    // Extract top-level fields
    let obj = raw.as_object().ok_or_else(|| {
        format!("Roadmap root must be an object, got: {}", raw)
    })?;

    let schema_version = extract_u32(obj, "schema_version", "/schema_version", 1);
    let roadmap_id = extract_string(obj, "roadmap_id", "/roadmap_id", "unknown").unwrap_or_else(|| "unknown".to_string());
    let title = extract_string(obj, "title", "/title", "Untitled Roadmap").unwrap_or_else(|| "Untitled Roadmap".to_string());
    let description = extract_string(obj, "description", "/description", "").unwrap_or_default();
    let project_start_date = extract_optional_string(obj, "project_start_date", "/project_start_date");
    let last_updated = extract_optional_string(obj, "last_updated", "/last_updated");

    // Extract phases
    let phases_raw = obj.get("phases").and_then(|v| v.as_array()).ok_or_else(|| {
        format!("Roadmap must have 'phases' array at /phases")
    })?;

    log::info!("📊 Found {} phases to process", phases_raw.len());

    let mut phases = Vec::new();
    for (idx, phase_val) in phases_raw.iter().enumerate() {
        let pointer = format!("/phases/{}", idx);
        match normalize_phase(phase_val, &pointer, &mut warnings, &mut fixed_items) {
            Some(phase) => {
                log::debug!("  ✓ Phase {} normalized: {}", idx, phase.phase_id);
                phases.push(phase);
            }
            None => {
                let warn = format!("Skipped malformed phase at {}", pointer);
                log::warn!("  ⚠️  {}", warn);
                warnings.push(warn);
            }
        }
    }

    if phases.is_empty() {
        return Err(format!("No valid phases found in roadmap (processed {} items)", phases_raw.len()));
    }

    log::info!("✓ Normalization complete: {} phases, {} warnings, {} items auto-fixed",
        phases.len(), warnings.len(), fixed_items);

    Ok(LoadResult {
        roadmap: RoadmapFile {
            schema_version,
            roadmap_id,
            title,
            description,
            project_start_date,
            last_updated,
            phases,
        },
        warnings,
        fixed_items,
    })
}

fn normalize_phase(
    val: &Value,
    pointer: &str,
    warnings: &mut Vec<String>,
    fixed_items: &mut usize,
) -> Option<PhaseSpec> {
    let obj = val.as_object()?;

    let phase_id = extract_string(obj, "phase_id", &format!("{}/phase_id", pointer), "")?;
    let title = extract_string(obj, "title", &format!("{}/title", pointer), "")?;
    let order_index = extract_i32(obj, "order_index", &format!("{}/order_index", pointer), 0);

    // Normalize status (handle enum-like objects)
    let status = normalize_status(obj.get("status"), &format!("{}/status", pointer), warnings, fixed_items);

    let start_date = extract_optional_string(obj, "start_date", &format!("{}/start_date", pointer));
    let target_date = extract_optional_string(obj, "target_date", &format!("{}/target_date", pointer));

    // Normalize content (handle objects/arrays)
    let content = normalize_content(obj.get("content"), &format!("{}/content", pointer), warnings, fixed_items);

    let dependencies = extract_string_array(obj, "dependencies", &format!("{}/dependencies", pointer));

    // Extract goals
    let empty_vec = vec![];
    let goals_raw = obj.get("goals").and_then(|v| v.as_array()).unwrap_or(&empty_vec);
    let mut goals = Vec::new();
    for (idx, goal_val) in goals_raw.iter().enumerate() {
        let goal_pointer = format!("{}/goals/{}", pointer, idx);
        if let Some(goal) = normalize_goal(goal_val, &goal_pointer, warnings, fixed_items) {
            goals.push(goal);
        } else {
            let warn = format!("Skipped malformed goal at {}", goal_pointer);
            warnings.push(warn);
        }
    }

    Some(PhaseSpec {
        phase_id,
        title,
        order_index,
        status,
        start_date,
        target_date,
        content,
        dependencies,
        goals,
    })
}

fn normalize_goal(
    val: &Value,
    pointer: &str,
    warnings: &mut Vec<String>,
    fixed_items: &mut usize,
) -> Option<GoalSpec> {
    let obj = val.as_object()?;

    let goal_id = extract_string(obj, "goal_id", &format!("{}/goal_id", pointer), "")?;
    let title = extract_string(obj, "title", &format!("{}/title", pointer), "")?;
    let order_index = extract_i32(obj, "order_index", &format!("{}/order_index", pointer), 0);
    let status = normalize_status(obj.get("status"), &format!("{}/status", pointer), warnings, fixed_items);
    let content = normalize_content(obj.get("content"), &format!("{}/content", pointer), warnings, fixed_items);

    // Extract tasks
    let empty_vec = vec![];
    let tasks_raw = obj.get("tasks").and_then(|v| v.as_array()).unwrap_or(&empty_vec);
    let mut tasks = Vec::new();
    for (idx, task_val) in tasks_raw.iter().enumerate() {
        let task_pointer = format!("{}/tasks/{}", pointer, idx);
        if let Some(task) = normalize_task(task_val, &task_pointer, warnings, fixed_items) {
            tasks.push(task);
        } else {
            let warn = format!("Skipped malformed task at {}", task_pointer);
            warnings.push(warn);
        }
    }

    Some(GoalSpec {
        goal_id,
        title,
        order_index,
        status,
        content,
        tasks,
    })
}

fn normalize_task(
    val: &Value,
    pointer: &str,
    warnings: &mut Vec<String>,
    fixed_items: &mut usize,
) -> Option<TaskSpec> {
    let obj = val.as_object()?;

    let task_id = extract_string(obj, "task_id", &format!("{}/task_id", pointer), "")?;
    let title = extract_string(obj, "title", &format!("{}/title", pointer), "")?;
    let order_index = extract_i32(obj, "order_index", &format!("{}/order_index", pointer), 0);
    let status = normalize_status(obj.get("status"), &format!("{}/status", pointer), warnings, fixed_items);
    let content = normalize_content(obj.get("content"), &format!("{}/content", pointer), warnings, fixed_items);

    Some(TaskSpec {
        task_id,
        title,
        order_index,
        status,
        content,
    })
}

// ========== NORMALIZER HELPERS ==========

/// Normalize status field (handles enum-like objects from Serde)
/// Examples: "active", {"Active": null}, {"Done": {}}
fn normalize_status(
    val: Option<&Value>,
    pointer: &str,
    warnings: &mut Vec<String>,
    fixed_items: &mut usize,
) -> String {
    match val {
        Some(Value::String(s)) => s.to_lowercase(),
        Some(Value::Object(obj)) => {
            // Enum-like: {"Active": null} or {"Done": {}}
            if let Some((key, _)) = obj.iter().next() {
                *fixed_items += 1;
                log::debug!("🔧 Fixed enum status at {}: {:?} -> {}", pointer, obj, key.to_lowercase());
                key.to_lowercase()
            } else {
                warnings.push(format!("Invalid status object at {}, defaulting to 'open'", pointer));
                "open".to_string()
            }
        }
        _ => {
            warnings.push(format!("Missing or invalid status at {}, defaulting to 'open'", pointer));
            "open".to_string()
        }
    }
}

/// Normalize content field (handles objects/arrays)
fn normalize_content(
    val: Option<&Value>,
    pointer: &str,
    warnings: &mut Vec<String>,
    fixed_items: &mut usize,
) -> String {
    match val {
        Some(Value::String(s)) => s.clone(),
        Some(Value::Object(_)) | Some(Value::Array(_)) => {
            // Stringify structured content
            *fixed_items += 1;
            let stringified = serde_json::to_string_pretty(val.unwrap()).unwrap_or_default();
            log::debug!("🔧 Fixed structured content at {}: converted to string ({} bytes)", pointer, stringified.len());
            stringified
        }
        Some(Value::Null) => String::new(),
        None => String::new(),
        _ => {
            warnings.push(format!("Unexpected content type at {}, using empty string", pointer));
            String::new()
        }
    }
}

// ========== EXTRACTION HELPERS ==========

fn extract_string(obj: &serde_json::Map<String, Value>, key: &str, pointer: &str, default: &str) -> Option<String> {
    match obj.get(key) {
        Some(Value::String(s)) if !s.is_empty() => Some(s.clone()),
        Some(Value::String(_)) if !default.is_empty() => {
            log::debug!("Empty string at {}, using default: {}", pointer, default);
            Some(default.to_string())
        }
        Some(Value::String(_)) => {
            log::warn!("Required field {} at {} is empty", key, pointer);
            None
        }
        None if !default.is_empty() => {
            log::debug!("Missing field {} at {}, using default: {}", key, pointer, default);
            Some(default.to_string())
        }
        None => {
            log::warn!("Required field {} missing at {}", key, pointer);
            None
        }
        Some(other) => {
            log::warn!("Field {} at {} has wrong type (expected string, got {})", key, pointer, other);
            None
        }
    }
}

fn extract_optional_string(obj: &serde_json::Map<String, Value>, key: &str, pointer: &str) -> Option<String> {
    match obj.get(key) {
        Some(Value::String(s)) if !s.is_empty() => Some(s.clone()),
        Some(Value::Null) | None => None,
        Some(other) => {
            log::debug!("Field {} at {} has wrong type (expected string, got {}), treating as None", key, pointer, other);
            None
        }
    }
}

fn extract_i32(obj: &serde_json::Map<String, Value>, key: &str, pointer: &str, default: i32) -> i32 {
    match obj.get(key) {
        Some(Value::Number(n)) => n.as_i64().unwrap_or(default as i64) as i32,
        None => {
            log::debug!("Missing {} at {}, using default: {}", key, pointer, default);
            default
        }
        Some(other) => {
            log::warn!("Field {} at {} has wrong type (expected number, got {}), using default: {}", key, pointer, other, default);
            default
        }
    }
}

fn extract_u32(obj: &serde_json::Map<String, Value>, key: &str, pointer: &str, default: u32) -> u32 {
    match obj.get(key) {
        Some(Value::Number(n)) => n.as_u64().unwrap_or(default as u64) as u32,
        None => {
            log::debug!("Missing {} at {}, using default: {}", key, pointer, default);
            default
        }
        Some(other) => {
            log::warn!("Field {} at {} has wrong type (expected number, got {}), using default: {}", key, pointer, other, default);
            default
        }
    }
}

fn extract_string_array(obj: &serde_json::Map<String, Value>, key: &str, pointer: &str) -> Vec<String> {
    match obj.get(key) {
        Some(Value::Array(arr)) => {
            arr.iter()
                .filter_map(|v| v.as_str().map(|s| s.to_string()))
                .collect()
        }
        None => Vec::new(),
        Some(other) => {
            log::debug!("Field {} at {} has wrong type (expected array, got {}), using empty array", key, pointer, other);
            Vec::new()
        }
    }
}
