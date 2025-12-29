use crate::domain::*;
use crate::errors::{MetaError, Result};
use crate::parser::frontmatter::FrontmatterParser;
use chrono::NaiveDate;
use std::fs;
use std::path::Path;

pub struct MarkdownParser;

impl MarkdownParser {
    pub fn parse_goal<P: AsRef<Path>>(path: P) -> Result<Goal> {
        let path = path.as_ref();
        let content = fs::read_to_string(path)?;
        let (frontmatter, body) = FrontmatterParser::parse(&content)?;

        let file_str = path.to_string_lossy().to_string();

        let goal_id = FrontmatterParser::require_string(&frontmatter, "goal_id", &file_str)?;

        if !Goal::validate_id(&goal_id) {
            return Err(MetaError::InvalidGoalId(goal_id));
        }

        let status_str = FrontmatterParser::require_string(&frontmatter, "status", &file_str)?;
        let status = GoalStatus::from_str(&status_str).ok_or_else(|| {
            MetaError::InvalidField {
                field: "status".to_string(),
                value: status_str.clone(),
                file: file_str.clone(),
            }
        })?;

        let title = FrontmatterParser::get_string(&frontmatter, "title")
            .unwrap_or_else(|| "Untitled".to_string());

        let phase = FrontmatterParser::get_u32(&frontmatter, "phase");
        let owner = FrontmatterParser::get_string(&frontmatter, "owner");
        let dependencies = FrontmatterParser::get_array(&frontmatter, "dependencies");
        let tags = FrontmatterParser::get_array(&frontmatter, "tags");

        Ok(Goal {
            goal_id,
            title,
            status,
            phase,
            owner,
            dependencies,
            tags,
            file_path: path.to_path_buf(),
            content: body,
        })
    }

    pub fn parse_decision<P: AsRef<Path>>(path: P) -> Result<Decision> {
        let path = path.as_ref();
        let content = fs::read_to_string(path)?;
        let (frontmatter, body) = FrontmatterParser::parse(&content)?;

        let file_str = path.to_string_lossy().to_string();

        let decision_id = FrontmatterParser::require_string(&frontmatter, "decision_id", &file_str)?;

        if !Decision::validate_id(&decision_id) {
            return Err(MetaError::InvalidDecisionId(decision_id));
        }

        let status_str = FrontmatterParser::require_string(&frontmatter, "status", &file_str)?;
        let status = DecisionStatus::from_str(&status_str).ok_or_else(|| {
            MetaError::InvalidField {
                field: "status".to_string(),
                value: status_str.clone(),
                file: file_str.clone(),
            }
        })?;

        let title = FrontmatterParser::get_string(&frontmatter, "title")
            .unwrap_or_else(|| "Untitled".to_string());

        let date_str = FrontmatterParser::require_string(&frontmatter, "date", &file_str)?;
        let date = NaiveDate::parse_from_str(&date_str, "%Y-%m-%d")
            .map_err(|_| MetaError::InvalidField {
                field: "date".to_string(),
                value: date_str,
                file: file_str.clone(),
            })?;

        let rationale = FrontmatterParser::get_string(&frontmatter, "rationale");

        Ok(Decision {
            decision_id,
            title,
            status,
            date,
            rationale,
            file_path: path.to_path_buf(),
            content: body,
        })
    }

    pub fn parse_daily<P: AsRef<Path>>(path: P) -> Result<DailyNote> {
        let path = path.as_ref();
        let content = fs::read_to_string(path)?;
        let (frontmatter, body) = FrontmatterParser::parse(&content)?;

        let file_str = path.to_string_lossy().to_string();

        let date_str = FrontmatterParser::require_string(&frontmatter, "date", &file_str)?;
        let date = NaiveDate::parse_from_str(&date_str, "%Y-%m-%d")
            .map_err(|_| MetaError::InvalidField {
                field: "date".to_string(),
                value: date_str,
                file: file_str.clone(),
            })?;

        let phase = FrontmatterParser::get_u32(&frontmatter, "phase");
        let goals_worked = FrontmatterParser::get_array(&frontmatter, "goals_worked");
        let decisions_made = FrontmatterParser::get_array(&frontmatter, "decisions_made");
        let divergences = FrontmatterParser::get_array(&frontmatter, "divergences");

        Ok(DailyNote {
            date,
            phase,
            goals_worked,
            decisions_made,
            divergences,
            file_path: path.to_path_buf(),
            content: body,
        })
    }
}
