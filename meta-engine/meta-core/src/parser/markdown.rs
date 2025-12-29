use crate::domain::*;
use crate::errors::{MetaError, Result};
use crate::parser::frontmatter::FrontmatterParser;
use crate::parser::LinkExtractor;
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

        // Accept both "goal_id" and "id" for backward compatibility
        let goal_id = FrontmatterParser::get_string(&frontmatter, "goal_id")
            .or_else(|| FrontmatterParser::get_string(&frontmatter, "id"))
            .ok_or_else(|| MetaError::MissingFrontmatter {
                field: "goal_id or id".to_string(),
                file: file_str.clone(),
            })?;

        if !Goal::validate_id(&goal_id) {
            return Err(MetaError::InvalidGoalId(goal_id));
        }

        let status_str = FrontmatterParser::require_string(&frontmatter, "status", &file_str)?;
        let status = GoalStatus::from_str(&status_str)
            .unwrap_or_else(|| GoalStatus::Unknown(status_str.clone()));

        let title = FrontmatterParser::get_string(&frontmatter, "title")
            .or_else(|| Self::heading_title(&body))
            .unwrap_or_else(|| goal_id.clone());

        let phase = FrontmatterParser::get_string(&frontmatter, "phase");
        let owner = FrontmatterParser::get_string(&frontmatter, "owner");

        let mut dependencies = FrontmatterParser::get_array(&frontmatter, "dependencies");
        if dependencies.is_empty() {
            dependencies = FrontmatterParser::get_array(&frontmatter, "depends_on");
        }
        let canon = FrontmatterParser::get_array(&frontmatter, "canon");
        let updated = FrontmatterParser::get_date(&frontmatter, "updated");
        let tags = FrontmatterParser::get_array(&frontmatter, "tags");

        Ok(Goal {
            goal_id,
            title,
            status,
            phase,
            owner,
            dependencies,
            canon,
            updated,
            tags,
            file_path: path.to_path_buf(),
            content: body,
        })
    }

    pub fn parse_decision<P: AsRef<Path>>(path: P) -> Result<Decision> {
        let path = path.as_ref();
        let content = fs::read_to_string(path)?;
        let (frontmatter, body) = FrontmatterParser::parse(&content)?;

        let decision_id = FrontmatterParser::get_string(&frontmatter, "decision_id")
            .or_else(|| FrontmatterParser::get_string(&frontmatter, "id"))
            .or_else(|| Self::derive_id_from_filename(path))
            .unwrap_or_else(|| path.file_stem().unwrap_or_default().to_string_lossy().to_string());

        if !Decision::validate_id(&decision_id) {
            return Err(MetaError::InvalidDecisionId(decision_id));
        }

        let status = FrontmatterParser::get_string(&frontmatter, "status")
            .and_then(|s| DecisionStatus::from_str(&s));

        let title = FrontmatterParser::get_string(&frontmatter, "title")
            .or_else(|| Self::heading_title(&body))
            .unwrap_or_else(|| decision_id.clone());

        let date = FrontmatterParser::get_date(&frontmatter, "date");
        let updated = FrontmatterParser::get_date(&frontmatter, "updated");
        let canon = FrontmatterParser::get_array(&frontmatter, "canon");
        let phase = FrontmatterParser::get_string(&frontmatter, "phase");
        let rationale = FrontmatterParser::get_string(&frontmatter, "rationale");

        Ok(Decision {
            decision_id,
            title,
            status,
            date,
            updated,
            canon,
            phase,
            rationale,
            file_path: path.to_path_buf(),
            content: body,
        })
    }

    pub fn parse_phase<P: AsRef<Path>>(path: P) -> Result<Phase> {
        let path = path.as_ref();
        let content = fs::read_to_string(path)?;
        let (frontmatter, body) = FrontmatterParser::parse(&content)?;
        let file_str = path.to_string_lossy().to_string();

        let phase_id = FrontmatterParser::get_string(&frontmatter, "phase_id")
            .or_else(|| FrontmatterParser::get_string(&frontmatter, "id"))
            .or_else(|| Self::derive_phase_id_from_filename(path))
            .unwrap_or_else(|| "P0".to_string());

        if phase_id.is_empty() {
            return Err(MetaError::MissingFrontmatter {
                field: "phase_id".to_string(),
                file: file_str,
            });
        }

        let title = FrontmatterParser::get_string(&frontmatter, "title")
            .or_else(|| Self::heading_title(&body))
            .unwrap_or_else(|| phase_id.clone());

        let status = FrontmatterParser::get_string(&frontmatter, "status");
        let depends_on = FrontmatterParser::get_array(&frontmatter, "depends_on");
        let owner = FrontmatterParser::get_string(&frontmatter, "owner");
        let updated = FrontmatterParser::get_date(&frontmatter, "updated");

        Ok(Phase {
            phase_id,
            title,
            status,
            depends_on,
            owner,
            updated,
            file_path: path.to_path_buf(),
            content: body,
        })
    }

    pub fn parse_audit<P: AsRef<Path>>(path: P) -> Result<AuditRecord> {
        let path = path.as_ref();
        let content = fs::read_to_string(path)?;
        let (frontmatter, body) = FrontmatterParser::parse(&content)?;

        let title = Self::heading_title(&body)
            .unwrap_or_else(|| path.file_stem().unwrap_or_default().to_string_lossy().to_string());
        let date = FrontmatterParser::get_date(&frontmatter, "date");
        let scope = FrontmatterParser::get_string(&frontmatter, "scope");
        let risk = FrontmatterParser::get_string(&frontmatter, "risk");
        let auditor = FrontmatterParser::get_string(&frontmatter, "auditor");

        let summary = body
            .lines()
            .skip_while(|line| line.trim().is_empty() || line.starts_with('#') || line.trim_start().starts_with("---"))
            .find(|line| !line.trim().is_empty())
            .map(|line| line.trim().to_string());

        Ok(AuditRecord {
            title,
            date,
            scope,
            risk,
            auditor,
            file_path: path.to_path_buf(),
            summary,
            content: body,
        })
    }

    pub fn parse_prompt<P: AsRef<Path>>(path: P) -> Result<Prompt> {
        let path = path.as_ref();
        let content = fs::read_to_string(path)?;
        let (frontmatter, body) = FrontmatterParser::parse(&content)?;

        let title = Self::heading_title(&body)
            .unwrap_or_else(|| path.file_stem().unwrap_or_default().to_string_lossy().to_string());

        let prompt_id = FrontmatterParser::get_string(&frontmatter, "prompt_id")
            .or_else(|| FrontmatterParser::get_string(&frontmatter, "id"));
        let agent = FrontmatterParser::get_string(&frontmatter, "agent");
        let purpose = FrontmatterParser::get_string(&frontmatter, "purpose");

        Ok(Prompt {
            prompt_id,
            agent,
            purpose,
            timestamp: None,
            prompt_text: None,
            response_text: None,
            title,
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

        let phase = FrontmatterParser::get_string(&frontmatter, "phase")
            .and_then(|value| value.trim_start_matches('P').parse::<u32>().ok())
            .or_else(|| FrontmatterParser::get_u32(&frontmatter, "phase"));

        let mode = FrontmatterParser::get_string(&frontmatter, "mode");
        let protocol = FrontmatterParser::get_string(&frontmatter, "protocol");

        let goals_worked = FrontmatterParser::get_array(&frontmatter, "goals_worked");
        let decisions_made = FrontmatterParser::get_array(&frontmatter, "decisions_made");
        let divergences = FrontmatterParser::get_array(&frontmatter, "divergences");
        let goals = if goals_worked.is_empty() {
            FrontmatterParser::get_array(&frontmatter, "goals")
        } else {
            goals_worked.clone()
        };
        let blockers = FrontmatterParser::get_array(&frontmatter, "blockers");
        let decisions = if decisions_made.is_empty() {
            FrontmatterParser::get_array(&frontmatter, "decisions")
        } else {
            decisions_made.clone()
        };

        let linked_goals = LinkExtractor::extract_all_links(&body);

        Ok(DailyNote {
            date,
            phase,
            mode,
            protocol,
            goals_worked,
            decisions_made,
            divergences,
            goals,
            blockers,
            decisions,
            linked_goals,
            file_path: path.to_path_buf(),
            content: body,
        })
    }

    fn heading_title(body: &str) -> Option<String> {
        body.lines()
            .find(|line| line.trim_start().starts_with('#'))
            .map(|line| line.trim_start_matches('#').trim().to_string())
    }

    fn derive_id_from_filename(path: &Path) -> Option<String> {
        path.file_stem()
            .and_then(|stem| stem.to_str())
            .map(|s| s.replace("DECISION —", "").trim().to_string())
    }

    fn derive_phase_id_from_filename(path: &Path) -> Option<String> {
        path.file_stem()
            .and_then(|stem| stem.to_str())
            .and_then(|name| {
                name.split_whitespace()
                    .find(|part| part.starts_with('P') && part.len() > 1)
                    .map(|s| s.to_string())
            })
    }
}
