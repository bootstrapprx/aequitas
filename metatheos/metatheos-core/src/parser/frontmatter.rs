use crate::errors::{MetaError, Result};
use serde_json::Value;
use std::collections::HashMap;

pub struct FrontmatterParser;

impl FrontmatterParser {
    /// Extract YAML frontmatter from markdown content
    /// Expected format:
    /// ---
    /// key: value
    /// ---
    /// content
    pub fn parse(content: &str) -> Result<(HashMap<String, Value>, String)> {
        let trimmed = content.trim_start();

        if !trimmed.starts_with("---") {
            return Ok((HashMap::new(), content.to_string()));
        }

        let rest = &trimmed[3..];

        if let Some(end_pos) = rest.find("\n---") {
            let yaml_content = &rest[..end_pos];
            let remaining = &rest[end_pos + 4..];

            let frontmatter: HashMap<String, Value> = serde_yaml::from_str(yaml_content)?;

            Ok((frontmatter, remaining.trim().to_string()))
        } else {
            Ok((HashMap::new(), content.to_string()))
        }
    }

    pub fn get_string(
        frontmatter: &HashMap<String, Value>,
        key: &str,
    ) -> Option<String> {
        frontmatter.get(key).and_then(|v| v.as_str()).map(String::from)
    }

    pub fn get_u32(
        frontmatter: &HashMap<String, Value>,
        key: &str,
    ) -> Option<u32> {
        frontmatter.get(key).and_then(|v| {
            v.as_u64().map(|n| n as u32)
        })
    }

    pub fn get_date(
        frontmatter: &HashMap<String, Value>,
        key: &str,
    ) -> Option<chrono::NaiveDate> {
        frontmatter.get(key).and_then(|v| v.as_str()).and_then(|value| {
            chrono::NaiveDate::parse_from_str(value, "%Y-%m-%d").ok()
        })
    }

    pub fn get_array(
        frontmatter: &HashMap<String, Value>,
        key: &str,
    ) -> Vec<String> {
        frontmatter
            .get(key)
            .and_then(|v| v.as_array())
            .map(|arr| {
                arr.iter()
                    .filter_map(|v| v.as_str().map(String::from))
                    .collect()
            })
            .unwrap_or_default()
    }

    pub fn require_string(
        frontmatter: &HashMap<String, Value>,
        key: &str,
        file: &str,
    ) -> Result<String> {
        Self::get_string(frontmatter, key).ok_or_else(|| MetaError::MissingFrontmatter {
            field: key.to_string(),
            file: file.to_string(),
        })
    }
}
