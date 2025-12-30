use crate::errors::Result;
use crate::governance::GovernanceContext;
use chrono::NaiveDate;
use std::path::PathBuf;

#[derive(Debug, Clone, Default)]
pub struct SummaryItem {
    pub id: String,
    pub status: Option<String>,
    pub phase: Option<String>,
    pub path: PathBuf,
    pub summary: String,
    pub updated: Option<NaiveDate>,
}

pub struct GovernanceIngestion;

impl GovernanceIngestion {
    pub fn load_goals(ctx: &GovernanceContext) -> Result<Vec<SummaryItem>> {
        let mut items: Vec<SummaryItem> = ctx
            .all_goals()
            .iter()
            .map(|g| SummaryItem {
                id: g.goal_id.clone(),
                status: Some(g.status.to_string()),
                phase: g.phase.clone(),
                path: g.file_path.clone(),
                summary: summarize(&g.title, &g.content),
                updated: g.updated,
            })
            .collect();
        items.sort_by(|a, b| a.id.cmp(&b.id));
        Ok(items)
    }

    pub fn load_decisions(ctx: &GovernanceContext) -> Result<Vec<SummaryItem>> {
        let mut items: Vec<SummaryItem> = ctx
            .all_decisions()
            .iter()
            .map(|d| SummaryItem {
                id: d.decision_id.clone(),
                status: d.status.as_ref().map(|s| s.to_string()),
                phase: d.phase.clone(),
                path: d.file_path.clone(),
                summary: summarize(&d.title, &d.content),
                updated: d.updated,
            })
            .collect();
        items.sort_by(|a, b| a.id.cmp(&b.id));
        Ok(items)
    }

    pub fn load_audits(ctx: &GovernanceContext) -> Result<Vec<SummaryItem>> {
        let mut items: Vec<SummaryItem> = ctx
            .all_audits()
            .iter()
            .map(|a| SummaryItem {
                id: a.file_path.file_stem().map(|s| s.to_string_lossy().to_string()).unwrap_or_default(),
                status: a.status.clone(),
                phase: None,
                path: a.file_path.clone(),
                summary: summarize(a.summary.as_deref().unwrap_or(&a.title), &a.content),
                updated: a.date,
            })
            .collect();
        items.sort_by(|a, b| a.id.cmp(&b.id));
        Ok(items)
    }

    pub fn load_daily_notes(ctx: &GovernanceContext, limit: usize) -> Result<Vec<SummaryItem>> {
        let mut notes: Vec<SummaryItem> = ctx
            .all_daily_notes()
            .into_iter()
            .map(|d| SummaryItem {
                id: d.date.format("%Y-%m-%d").to_string(),
                status: d.mode.clone(),
                phase: d.phase.map(|p| format!("P{}", p)),
                path: d.file_path.clone(),
                summary: summarize(&d.mode.clone().unwrap_or_else(|| "daily".to_string()), &d.content),
                updated: Some(d.date),
            })
            .collect();

        notes.sort_by(|a, b| b.id.cmp(&a.id));
        notes.truncate(limit);
        Ok(notes)
    }

    pub fn filter_goals_by_ids(ctx: &GovernanceContext, ids: &[String]) -> Result<Vec<SummaryItem>> {
        let set: std::collections::HashSet<String> = ids.iter().map(|s| s.to_lowercase()).collect();
        Ok(Self::load_goals(ctx)?
            .into_iter()
            .filter(|g| set.contains(&g.id.to_lowercase()))
            .collect())
    }

    pub fn filter_decisions_by_ids(ctx: &GovernanceContext, ids: &[String]) -> Result<Vec<SummaryItem>> {
        let set: std::collections::HashSet<String> = ids.iter().map(|s| s.to_lowercase()).collect();
        Ok(Self::load_decisions(ctx)?
            .into_iter()
            .filter(|d| set.contains(&d.id.to_lowercase()))
            .collect())
    }

    pub fn filter_audits_by_ids(ctx: &GovernanceContext, ids: &[String]) -> Result<Vec<SummaryItem>> {
        let set: std::collections::HashSet<String> = ids.iter().map(|s| s.to_lowercase()).collect();
        Ok(Self::load_audits(ctx)?
            .into_iter()
            .filter(|a| set.contains(&a.id.to_lowercase()))
            .collect())
    }

    pub fn active_phase_summary(ctx: &GovernanceContext) -> Option<SummaryItem> {
        ctx.active_phase().map(|p| SummaryItem {
            id: p.phase_id.clone(),
            status: Some(p.status.clone()),
            phase: Some(p.phase_id.clone()),
            path: p.file_path.clone(),
            summary: summarize(&p.title, &p.content),
            updated: None,
        })
    }
}

fn summarize(title: &str, body: &str) -> String {
    let mut summary = title.trim().to_string();
    if summary.is_empty() {
        summary = "untitled".to_string();
    }

    let first_line = body.lines().find(|l| !l.trim().is_empty()).unwrap_or("");
    if !first_line.is_empty() && !summary.eq_ignore_ascii_case(first_line) {
        summary = format!("{} — {}", summary, first_line.trim());
    }

    if summary.len() > 240 {
        summary.truncate(240);
    }

    summary
}
