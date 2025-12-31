use crate::domain::{Goal, Phase};
use crate::errors::{MetaError, Result};
use serde_yaml;
use std::collections::HashMap;

pub struct FrontmatterSerializer;

impl FrontmatterSerializer {
    /// Serialize a Goal to YAML frontmatter
    pub fn goal_to_yaml(goal: &Goal) -> Result<String> {
        let mut map = HashMap::new();

        map.insert("goal_id".to_string(), serde_yaml::Value::String(goal.goal_id.clone()));
        map.insert("title".to_string(), serde_yaml::Value::String(goal.title.clone()));
        map.insert("status".to_string(), serde_yaml::Value::String(goal.status.as_str().to_string()));

        if let Some(ref phase) = goal.phase {
            map.insert("phase".to_string(), serde_yaml::Value::String(phase.clone()));
        }

        if let Some(ref owner) = goal.owner {
            map.insert("owner".to_string(), serde_yaml::Value::String(owner.clone()));
        }

        if !goal.dependencies.is_empty() {
            let deps: Vec<serde_yaml::Value> = goal.dependencies
                .iter()
                .map(|d| serde_yaml::Value::String(d.clone()))
                .collect();
            map.insert("dependencies".to_string(), serde_yaml::Value::Sequence(deps));
        }

        if !goal.canon.is_empty() {
            let canon: Vec<serde_yaml::Value> = goal.canon
                .iter()
                .map(|c| serde_yaml::Value::String(c.clone()))
                .collect();
            map.insert("canon".to_string(), serde_yaml::Value::Sequence(canon));
        }

        if !goal.tags.is_empty() {
            let tags: Vec<serde_yaml::Value> = goal.tags
                .iter()
                .map(|t| serde_yaml::Value::String(t.clone()))
                .collect();
            map.insert("tags".to_string(), serde_yaml::Value::Sequence(tags));
        }

        if let Some(updated) = goal.updated {
            map.insert("updated".to_string(), serde_yaml::Value::String(updated.to_string()));
        }

        // Convert HashMap<String, Value> to Mapping
        let mapping = serde_yaml::Mapping::from_iter(
            map.into_iter().map(|(k, v)| (serde_yaml::Value::String(k), v))
        );
        let value = serde_yaml::Value::Mapping(mapping);
        serde_yaml::to_string(&value)
            .map_err(|e| MetaError::ParseError(format!("Failed to serialize goal frontmatter: {}", e)))
    }

    /// Serialize a Phase to YAML frontmatter
    pub fn phase_to_yaml(phase: &Phase) -> Result<String> {
        let mut map = HashMap::new();

        map.insert("phase_id".to_string(), serde_yaml::Value::String(phase.phase_id.clone()));
        map.insert("title".to_string(), serde_yaml::Value::String(phase.title.clone()));
        map.insert("status".to_string(), serde_yaml::Value::String(phase.status.clone()));

        if let Some(start) = phase.start_date {
            map.insert("start_date".to_string(), serde_yaml::Value::String(start.to_string()));
        }

        if let Some(target) = phase.target_date {
            map.insert("target_date".to_string(), serde_yaml::Value::String(target.to_string()));
        }

        if !phase.dependencies.is_empty() {
            let deps: Vec<serde_yaml::Value> = phase.dependencies
                .iter()
                .map(|d| serde_yaml::Value::String(d.clone()))
                .collect();
            map.insert("dependencies".to_string(), serde_yaml::Value::Sequence(deps));
        }

        // Convert HashMap<String, Value> to Mapping
        let mapping = serde_yaml::Mapping::from_iter(
            map.into_iter().map(|(k, v)| (serde_yaml::Value::String(k), v))
        );
        let value = serde_yaml::Value::Mapping(mapping);
        serde_yaml::to_string(&value)
            .map_err(|e| MetaError::ParseError(format!("Failed to serialize phase frontmatter: {}", e)))
    }

    /// Build complete markdown file with frontmatter and content
    pub fn build_document(frontmatter: &str, content: &str) -> String {
        format!("---\n{}---\n\n{}", frontmatter, content.trim())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;
    use crate::GoalStatus;
    use chrono::NaiveDate;

    #[test]
    fn test_goal_frontmatter_serialization() {
        let goal = Goal {
            goal_id: "goal-test".to_string(),
            title: "Test Goal".to_string(),
            status: GoalStatus::Active,
            phase: Some("P1".to_string()),
            owner: Some("@alice".to_string()),
            parent_id: None,
            level: Some("goal".to_string()),
            dependencies: vec!["goal-dep1".to_string(), "goal-dep2".to_string()],
            canon: vec!["doc.md".to_string()],
            tags: vec!["tag1".to_string(), "tag2".to_string()],
            updated: Some(NaiveDate::from_ymd_opt(2025, 12, 29).unwrap()),
            file_path: PathBuf::from("test.md"),
            content: "Test content".to_string(),
        };

        let yaml = FrontmatterSerializer::goal_to_yaml(&goal).unwrap();

        assert!(yaml.contains("goal_id: goal-test"));
        assert!(yaml.contains("title: Test Goal"));
        assert!(yaml.contains("status: active"));
        assert!(yaml.contains("phase: P1"));
        assert!(yaml.contains("owner: '@alice'"));
        assert!(yaml.contains("- goal-dep1"));
        assert!(yaml.contains("- goal-dep2"));
    }

    #[test]
    fn test_build_document() {
        let frontmatter = "goal_id: test\ntitle: Test\n";
        let content = "# Test Goal\n\nContent here";

        let doc = FrontmatterSerializer::build_document(frontmatter, content);

        assert!(doc.starts_with("---\n"));
        assert!(doc.contains("---\n\n# Test Goal"));
    }
}
