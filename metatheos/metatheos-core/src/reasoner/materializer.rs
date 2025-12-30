use crate::domain::{Goal, GoalStatus};
use crate::errors::{MetaError, Result};
use crate::writer::FrontmatterSerializer;
use serde_json::Value;
use std::path::{Path, PathBuf};

use crate::reasoner::intent::Intent;

#[derive(Debug, Clone)]
pub struct DraftArtifact {
    pub intent: Intent,
    pub target_path: PathBuf,
    pub frontmatter: String,
    pub body: String,
}

pub struct MarkdownMaterializer;

impl MarkdownMaterializer {
    pub fn to_draft(doc: &Value, governance_root: &Path, ctx: &crate::governance::GovernanceContext) -> Result<DraftArtifact> {
        let intent_str = doc["intent"]
            .as_str()
            .ok_or_else(|| MetaError::ValidationError("Missing intent field".to_string()))?;

        let intent = match intent_str {
            "draft_goal" => Intent::DraftGoal,
            "update_goal" => Intent::UpdateGoal,
            "draft_decision" => Intent::DraftDecision,
            "draft_audit" => Intent::DraftAudit,
            "summarize_state" => Intent::SummarizeState,
            "analyze_blockers" => Intent::AnalyzeBlockers,
            "explain_phase" => Intent::ExplainPhase,
            other => {
                return Err(MetaError::ValidationError(format!(
                    "Unknown intent {}",
                    other
                )))
            }
        };

        match intent {
            Intent::DraftGoal => Self::goal_draft(doc, governance_root),
            Intent::UpdateGoal => Self::goal_update(doc, governance_root, ctx),
            Intent::DraftDecision => Self::decision_draft(doc, governance_root),
            Intent::DraftAudit => Self::audit_draft(doc, governance_root),
            Intent::SummarizeState | Intent::AnalyzeBlockers | Intent::ExplainPhase => {
                Err(MetaError::ValidationError("No materialization for analysis-only intents".to_string()))
            }
        }
    }

    fn goal_draft(doc: &Value, root: &Path) -> Result<DraftArtifact> {
        let id = doc["id"]
            .as_str()
            .ok_or_else(|| MetaError::ValidationError("Goal id missing".to_string()))?;
        let title = doc["title"]
            .as_str()
            .unwrap_or("Untitled Goal")
            .to_string();
        let status_str = doc["status"].as_str().unwrap_or("planned");
        let status = GoalStatus::from_str(status_str).unwrap_or(GoalStatus::Planned);
        let phase = doc["phase"].as_str().map(|s| s.to_string());
        let depends = doc["depends_on"]
            .as_array()
            .map(|arr| {
                arr.iter()
                    .filter_map(|v| v.as_str().map(|s| s.to_string()))
                    .collect::<Vec<String>>()
            })
            .unwrap_or_default();
        let canon = doc["canon_refs"]
            .as_array()
            .map(|arr| {
                arr.iter()
                    .filter_map(|v| v.as_str().map(|s| s.to_string()))
                    .collect::<Vec<String>>()
            })
            .unwrap_or_default();
        let body = doc["body"].as_str().unwrap_or("").to_string();

        let target_path = ensure_under_root(
            root,
            root.join("03_GOALS_EPICS").join(format!("{}.md", id)),
        )?;

        let goal = Goal {
            goal_id: id.to_string(),
            title: title.clone(),
            status,
            phase,
            owner: None,
            dependencies: depends,
            canon,
            updated: None,
            tags: vec![],
            file_path: target_path.clone(),
            content: body.clone(),
        };

        let fm = FrontmatterSerializer::goal_to_yaml(&goal)?;
        Ok(DraftArtifact {
            intent: Intent::DraftGoal,
            target_path,
            frontmatter: fm,
            body,
        })
    }

    fn goal_update(doc: &Value, _root: &Path, ctx: &crate::governance::GovernanceContext) -> Result<DraftArtifact> {
        let id = doc["id"]
            .as_str()
            .ok_or_else(|| MetaError::ValidationError("Goal id missing".to_string()))?;
        let goal = ctx.get_goal(id).ok_or_else(|| MetaError::ValidationError("Goal not found for update".to_string()))?;
        let title = goal.title.clone();
        let status_str = doc["status"].as_str().unwrap_or(goal.status.as_str());
        let status = GoalStatus::from_str(status_str).unwrap_or(goal.status.clone());
        let phase = doc["phase"].as_str().map(|s| s.to_string()).or(goal.phase.clone());
        let depends = doc["depends_on"]
            .as_array()
            .map(|arr| {
                arr.iter()
                    .filter_map(|v| v.as_str().map(|s| s.to_string()))
                    .collect::<Vec<String>>()
            })
            .unwrap_or(goal.dependencies.clone());
        let canon = doc["canon_refs"]
            .as_array()
            .map(|arr| {
                arr.iter()
                    .filter_map(|v| v.as_str().map(|s| s.to_string()))
                    .collect::<Vec<String>>()
            })
            .unwrap_or(goal.canon.clone());
        let body = doc["body"].as_str().unwrap_or(&goal.content).to_string();

        let target_path = goal.file_path.clone();

        let goal_struct = Goal {
            goal_id: id.to_string(),
            title: title.clone(),
            status,
            phase,
            owner: goal.owner.clone(),
            dependencies: depends,
            canon,
            updated: goal.updated,
            tags: goal.tags.clone(),
            file_path: target_path.clone(),
            content: body.clone(),
        };

        let fm = FrontmatterSerializer::goal_to_yaml(&goal_struct)?;
        Ok(DraftArtifact {
            intent: Intent::UpdateGoal,
            target_path,
            frontmatter: fm,
            body,
        })
    }

    fn decision_draft(doc: &Value, root: &Path) -> Result<DraftArtifact> {
        let id = doc["id"]
            .as_str()
            .ok_or_else(|| MetaError::ValidationError("Decision id missing".to_string()))?;
        let title = doc["title"]
            .as_str()
            .unwrap_or("Untitled Decision")
            .to_string();
        let status = doc["status"].as_str().unwrap_or("draft").to_string();
        let phase = doc["phase"].as_str().unwrap_or("P1").to_string();
        let canon = doc["canon_refs"]
            .as_array()
            .map(|arr| {
                arr.iter()
                    .filter_map(|v| v.as_str().map(|s| s.to_string()))
                    .collect::<Vec<String>>()
            })
            .unwrap_or_default();
        let impacts = doc["impacts"]
            .as_array()
            .map(|arr| {
                arr.iter()
                    .filter_map(|v| v.as_str().map(|s| s.to_string()))
                    .collect::<Vec<String>>()
            })
            .unwrap_or_default();
        let rationale = doc["rationale"].as_str().unwrap_or("").to_string();
        let body = doc["body"].as_str().unwrap_or("").to_string();

        let target_path = ensure_under_root(
            root,
            root.join("04_DECISIONS").join(format!("{}.md", id)),
        )?;

        let fm = build_frontmatter(&[
            ("decision_id", id),
            ("title", &title),
            ("status", &status),
            ("phase", &phase),
            ("rationale", &rationale),
        ]) + &collection_field("canon", &canon) + &collection_field("impacts", &impacts);

        Ok(DraftArtifact {
            intent: Intent::DraftDecision,
            target_path,
            frontmatter: fm,
            body,
        })
    }

    fn audit_draft(doc: &Value, root: &Path) -> Result<DraftArtifact> {
        let id = doc["id"]
            .as_str()
            .ok_or_else(|| MetaError::ValidationError("Audit id missing".to_string()))?;
        let severity = doc["severity"].as_str().unwrap_or("info").to_string();
        let remediation = doc["remediation"].as_str().unwrap_or("").to_string();
        let findings = doc["findings"]
            .as_array()
            .map(|arr| {
                arr.iter()
                    .filter_map(|v| v.as_str().map(|s| s.to_string()))
                    .collect::<Vec<String>>()
            })
            .unwrap_or_default();
        let scope = doc
            .get("target")
            .or_else(|| doc.get("scope"))
            .and_then(|v| v.as_array())
            .map(|arr| {
                arr.iter()
                    .filter_map(|v| v.as_str().map(|s| s.to_string()))
                    .collect::<Vec<String>>()
            })
            .unwrap_or_default();
        let canon = doc["canon_refs"]
            .as_array()
            .map(|arr| {
                arr.iter()
                    .filter_map(|v| v.as_str().map(|s| s.to_string()))
                    .collect::<Vec<String>>()
            })
            .unwrap_or_default();
        let body = doc["body"].as_str().unwrap_or("").to_string();

        let target_path =
            ensure_under_root(root, root.join("05_AUDITS").join(format!("{}.md", id)))?;

        let mut fm = build_frontmatter(&[
            ("id", id),
            ("severity", &severity),
            ("remediation", &remediation),
        ]);
        fm.push_str(&collection_field("target", &scope));
        fm.push_str(&collection_field("canon", &canon));
        fm.push_str(&collection_field("findings", &findings));

        Ok(DraftArtifact {
            intent: Intent::DraftAudit,
            target_path,
            frontmatter: fm,
            body,
        })
    }

}

fn ensure_under_root(root: &Path, target: PathBuf) -> Result<PathBuf> {
    let norm_root = root.canonicalize().unwrap_or_else(|_| root.to_path_buf());
    let norm_target = target.clone();
    if !norm_target.starts_with(&norm_root) {
        return Err(MetaError::ValidationError(
            "Target path would escape governance root".to_string(),
        ));
    }
    Ok(target)
}

fn build_frontmatter(pairs: &[(&str, &str)]) -> String {
    let mut out = String::new();
    for (k, v) in pairs {
        if !v.is_empty() {
            out.push_str(&format!("{}: {}\n", k, v));
        }
    }
    out
}

fn collection_field(key: &str, values: &[String]) -> String {
    if values.is_empty() {
        return String::new();
    }
    let mut out = format!("{}:\n", key);
    for v in values {
        out.push_str(&format!("- {}\n", v));
    }
    out
}
