use chrono::NaiveDate;
use serde::{de::Deserializer, Deserialize, Serialize};
use std::path::PathBuf;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DailyNote {
    pub date: NaiveDate,
    #[serde(default)]
    pub phase: Option<String>,
    #[serde(default)]
    pub mode: Option<String>,
    #[serde(default)]
    pub protocol: Option<String>,
    #[serde(default, deserialize_with = "deserialize_vec")]
    pub goals_worked: Vec<String>,
    #[serde(default, deserialize_with = "deserialize_vec")]
    pub decisions_made: Vec<String>,
    #[serde(default, deserialize_with = "deserialize_vec")]
    pub divergences: Vec<String>,
    #[serde(default, deserialize_with = "deserialize_vec")]
    pub goals: Vec<String>,
    #[serde(default, deserialize_with = "deserialize_vec")]
    pub blockers: Vec<String>,
    #[serde(default, deserialize_with = "deserialize_vec")]
    pub decisions: Vec<String>,
    #[serde(default, deserialize_with = "deserialize_vec")]
    pub linked_goals: Vec<String>,
    #[serde(default, deserialize_with = "deserialize_path")]
    pub file_path: PathBuf,
    #[serde(default, deserialize_with = "deserialize_string")]
    pub content: String,
    #[serde(flatten, default)]
    pub extra: std::collections::HashMap<String, serde_json::Value>,
}

fn deserialize_vec<'de, D>(deserializer: D) -> Result<Vec<String>, D::Error>
where
    D: Deserializer<'de>,
{
    Ok(Option::<Vec<String>>::deserialize(deserializer)?.unwrap_or_default())
}

fn deserialize_path<'de, D>(deserializer: D) -> Result<PathBuf, D::Error>
where
    D: Deserializer<'de>,
{
    Ok(Option::<String>::deserialize(deserializer)?
        .map(PathBuf::from)
        .unwrap_or_default())
}

fn deserialize_string<'de, D>(deserializer: D) -> Result<String, D::Error>
where
    D: Deserializer<'de>,
{
    Ok(Option::<String>::deserialize(deserializer)?.unwrap_or_default())
}

impl DailyNote {
    pub fn file_name(date: &NaiveDate) -> String {
        format!("{}.md", date.format("%Y-%m-%d"))
    }

    pub fn validate_file_name(name: &str) -> bool {
        name.ends_with(".md") && NaiveDate::parse_from_str(&name[..10], "%Y-%m-%d").is_ok()
    }
}
