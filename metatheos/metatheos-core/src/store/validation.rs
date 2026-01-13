/// Input validation layer for Metatheos database operations
/// Prevents invalid data from reaching SurrealDB and causing corruption
use crate::errors::{MetaError, Result};
use serde_json::Value;

/// Validate phase data before database write
pub fn validate_phase_input(data: &Value) -> Result<()> {
    let obj = data.as_object()
        .ok_or_else(|| MetaError::ValidationError("Phase data must be an object".to_string()))?;

    // Required fields
    if !obj.contains_key("id") || obj["id"].as_str().is_none() {
        return Err(MetaError::ValidationError("Phase must have 'id' field".to_string()));
    }

    if !obj.contains_key("phase_id") || obj["phase_id"].as_str().is_none() {
        return Err(MetaError::ValidationError("Phase must have 'phase_id' field".to_string()));
    }

    if !obj.contains_key("title") || obj["title"].as_str().is_none() {
        return Err(MetaError::ValidationError("Phase must have 'title' field".to_string()));
    }

    // Status validation
    if let Some(status) = obj.get("status").and_then(|v| v.as_str()) {
        const VALID_STATUSES: &[&str] = &["planned", "active", "closed", "archived"];
        if !VALID_STATUSES.contains(&status) {
            return Err(MetaError::ValidationError(
                format!("Invalid phase status '{}'. Must be one of: {:?}", status, VALID_STATUSES)
            ));
        }
    }

    // Array field validation
    if let Some(deps) = obj.get("dependencies") {
        if !deps.is_array() {
            return Err(MetaError::ValidationError(
                "Phase 'dependencies' must be an array".to_string()
            ));
        }
    }

    Ok(())
}

/// Validate goal data before database write
pub fn validate_goal_input(data: &Value) -> Result<()> {
    let obj = data.as_object()
        .ok_or_else(|| MetaError::ValidationError("Goal data must be an object".to_string()))?;

    // Required fields
    if !obj.contains_key("id") || obj["id"].as_str().is_none() {
        return Err(MetaError::ValidationError("Goal must have 'id' field".to_string()));
    }

    if !obj.contains_key("phase_id") || obj["phase_id"].as_str().is_none() {
        return Err(MetaError::ValidationError("Goal must have 'phase_id' field".to_string()));
    }

    if !obj.contains_key("title") || obj["title"].as_str().is_none() {
        return Err(MetaError::ValidationError("Goal must have 'title' field".to_string()));
    }

    if !obj.contains_key("status") || obj["status"].as_str().is_none() {
        return Err(MetaError::ValidationError("Goal must have 'status' field".to_string()));
    }

    // Priority validation
    if let Some(priority) = obj.get("priority").and_then(|v| v.as_str()) {
        const VALID_PRIORITIES: &[&str] = &["low", "normal", "high", "critical"];
        if !VALID_PRIORITIES.contains(&priority) {
            return Err(MetaError::ValidationError(
                format!("Invalid goal priority '{}'. Must be one of: {:?}", priority, VALID_PRIORITIES)
            ));
        }
    }

    // Array field validation
    for field_name in &["dependencies", "tags"] {
        if let Some(field) = obj.get(*field_name) {
            if !field.is_array() {
                return Err(MetaError::ValidationError(
                    format!("Goal '{}' must be an array", field_name)
                ));
            }
        }
    }

    Ok(())
}

/// Validate work item data before database write
pub fn validate_work_item_input(data: &Value) -> Result<()> {
    let obj = data.as_object()
        .ok_or_else(|| MetaError::ValidationError("Work item data must be an object".to_string()))?;

    // Required fields
    if !obj.contains_key("id") || obj["id"].as_str().is_none() {
        return Err(MetaError::ValidationError("Work item must have 'id' field".to_string()));
    }

    if !obj.contains_key("goal_id") || obj["goal_id"].as_str().is_none() {
        return Err(MetaError::ValidationError("Work item must have 'goal_id' field".to_string()));
    }

    if !obj.contains_key("level") || obj["level"].as_str().is_none() {
        return Err(MetaError::ValidationError("Work item must have 'level' field".to_string()));
    }

    if !obj.contains_key("title") || obj["title"].as_str().is_none() {
        return Err(MetaError::ValidationError("Work item must have 'title' field".to_string()));
    }

    if !obj.contains_key("status") || obj["status"].as_str().is_none() {
        return Err(MetaError::ValidationError("Work item must have 'status' field".to_string()));
    }

    // Level validation
    if let Some(level) = obj.get("level").and_then(|v| v.as_str()) {
        const VALID_LEVELS: &[&str] = &["goal", "subgoal", "task"];
        if !VALID_LEVELS.contains(&level) {
            return Err(MetaError::ValidationError(
                format!("Invalid work item level '{}'. Must be one of: {:?}", level, VALID_LEVELS)
            ));
        }
    }

    Ok(())
}

/// Validate day data before database write
pub fn validate_day_input(data: &Value) -> Result<()> {
    let obj = data.as_object()
        .ok_or_else(|| MetaError::ValidationError("Day data must be an object".to_string()))?;

    // Required fields
    if !obj.contains_key("id") || obj["id"].as_str().is_none() {
        return Err(MetaError::ValidationError("Day must have 'id' field (YYYY-MM-DD format)".to_string()));
    }

    // Validate date format (basic check)
    if let Some(id) = obj.get("id").and_then(|v| v.as_str()) {
        if id.len() != 10 || !id.chars().nth(4).map(|c| c == '-').unwrap_or(false) {
            return Err(MetaError::ValidationError(
                "Day 'id' must be in YYYY-MM-DD format".to_string()
            ));
        }
    }

    // Array field validation
    for field_name in &["goals", "focus_areas"] {
        if let Some(field) = obj.get(*field_name) {
            if !field.is_array() {
                return Err(MetaError::ValidationError(
                    format!("Day '{}' must be an array", field_name)
                ));
            }
        }
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn test_valid_phase() {
        let data = json!({
            "id": "P0",
            "phase_id": "P0",
            "title": "Foundation",
            "status": "active"
        });
        assert!(validate_phase_input(&data).is_ok());
    }

    #[test]
    fn test_invalid_phase_status() {
        let data = json!({
            "id": "P0",
            "phase_id": "P0",
            "title": "Foundation",
            "status": "invalid"
        });
        assert!(validate_phase_input(&data).is_err());
    }

    #[test]
    fn test_missing_phase_id() {
        let data = json!({
            "title": "Foundation",
            "status": "active"
        });
        assert!(validate_phase_input(&data).is_err());
    }

    #[test]
    fn test_valid_goal() {
        let data = json!({
            "id": "G-P0-01",
            "phase_id": "P0",
            "title": "Test goal",
            "status": "open",
            "priority": "normal"
        });
        assert!(validate_goal_input(&data).is_ok());
    }

    #[test]
    fn test_invalid_goal_priority() {
        let data = json!({
            "id": "G-P0-01",
            "phase_id": "P0",
            "title": "Test goal",
            "status": "open",
            "priority": "invalid"
        });
        assert!(validate_goal_input(&data).is_err());
    }
}
