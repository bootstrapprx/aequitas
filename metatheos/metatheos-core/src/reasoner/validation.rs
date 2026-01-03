use crate::domain::{Decision, Goal};
use crate::governance::GovernanceContext;
use crate::reasoner::intent::Intent;
use regex::Regex;
use serde_json::Value;
use std::collections::HashSet;

#[derive(Debug, Clone, Default)]
pub struct ValidationReport {
    pub valid: bool,
    pub errors: Vec<String>,
    pub warnings: Vec<String>,
}

impl ValidationReport {
    pub fn error(msg: impl Into<String>) -> Self {
        Self {
            valid: false,
            errors: vec![msg.into()],
            warnings: Vec::new(),
        }
    }

    pub fn ok() -> Self {
        Self {
            valid: true,
            errors: Vec::new(),
            warnings: Vec::new(),
        }
    }

    pub fn merge(mut self, other: ValidationReport) -> Self {
        self.errors.extend(other.errors);
        self.warnings.extend(other.warnings);
        self.valid = self.valid && other.valid && self.errors.is_empty();
        self
    }
}

pub struct ValidationLayer;

impl ValidationLayer {
    pub fn validate(doc: &Value, intent: &Intent, ctx: &GovernanceContext) -> ValidationReport {
        if doc.get("intent").and_then(|v| v.as_str()).is_none() {
            return ValidationReport::error("Missing intent field");
        }

        let mut report = ValidationReport::ok();

        // Disallow paths or filenames provided by model
        for key in ["path", "file", "filename", "filepath"].iter() {
            if doc.get(*key).is_some() {
                report.valid = false;
                report
                    .errors
                    .push(format!("Model must not propose {}.", key));
            }
        }

        let canon_set: HashSet<String> = ctx
            .state
            .canon_docs
            .iter()
            .map(|c| c.title.to_lowercase())
            .collect();

        match intent {
            Intent::DraftGoal => {
                report = report.merge(Self::validate_goal(doc, ctx));
                report = report.merge(Self::validate_canon(doc, &canon_set));
            }
            Intent::UpdateGoal => {
                report = report.merge(Self::validate_goal_update(doc, ctx));
                report = report.merge(Self::validate_canon(doc, &canon_set));
            }
            Intent::DraftDecision => {
                report = report.merge(Self::validate_decision(doc, ctx));
                report = report.merge(Self::validate_canon(doc, &canon_set));
            }
            Intent::DraftAudit => {
                report = report.merge(Self::validate_audit(doc, ctx));
                report = report.merge(Self::validate_canon(doc, &canon_set));
            }
            Intent::SummarizeState | Intent::AnalyzeBlockers | Intent::ExplainPhase => {}
        }

        if !report.errors.is_empty() {
            report.valid = false;
        }

        report
    }

    fn validate_goal(doc: &Value, ctx: &GovernanceContext) -> ValidationReport {
        let mut report = ValidationReport::ok();
        let id = doc["id"].as_str().unwrap_or_default();
        if !Goal::validate_id(id) || !id.starts_with("G-") {
            report
                .errors
                .push("Goal id must look like G-###".to_string());
        }
        if ctx.get_goal(id).is_some() {
            report.errors.push(format!("Goal id {} already exists", id));
        }
        let phase = doc["phase"].as_str().unwrap_or_default();
        if !phase.starts_with('P') {
            report.errors.push("Phase must look like P#".to_string());
        }
        if let Some(deps) = doc.get("depends_on").and_then(|v| v.as_array()) {
            for dep in deps {
                if let Some(dep_id) = dep.as_str() {
                    if ctx.get_goal(dep_id).is_none() {
                        report
                            .errors
                            .push(format!("Dependency {} does not exist", dep_id));
                    }
                }
            }
        }
        report
    }

    fn validate_goal_update(doc: &Value, ctx: &GovernanceContext) -> ValidationReport {
        let mut report = ValidationReport::ok();
        let id = doc["id"].as_str().unwrap_or_default();
        if !Goal::validate_id(id) || !id.starts_with("G-") {
            report
                .errors
                .push("Goal id must look like G-###".to_string());
        }
        if ctx.get_goal(id).is_none() {
            report
                .errors
                .push(format!("Goal id {} not found for update", id));
        }
        if let Some(deps) = doc.get("depends_on").and_then(|v| v.as_array()) {
            for dep in deps {
                if let Some(dep_id) = dep.as_str() {
                    if ctx.get_goal(dep_id).is_none() {
                        report
                            .errors
                            .push(format!("Dependency {} does not exist", dep_id));
                    }
                }
            }
        }
        report
    }

    fn validate_decision(doc: &Value, ctx: &GovernanceContext) -> ValidationReport {
        let mut report = ValidationReport::ok();
        let id = doc["id"].as_str().unwrap_or_default();
        if !Decision::validate_id(id) || !id.starts_with("D-") {
            report
                .errors
                .push("Decision id must look like D-###".to_string());
        }
        if ctx.get_decision(id).is_some() {
            report
                .errors
                .push(format!("Decision id {} already exists", id));
        }
        if let Some(impacts) = doc.get("impacts").and_then(|v| v.as_array()) {
            for g in impacts {
                if let Some(goal_id) = g.as_str() {
                    if ctx.get_goal(goal_id).is_none() {
                        report
                            .errors
                            .push(format!("Impacted goal {} not found", goal_id));
                    }
                }
            }
        }
        report
    }

    fn validate_audit(doc: &Value, ctx: &GovernanceContext) -> ValidationReport {
        let mut report = ValidationReport::ok();
        let id = doc["id"].as_str().unwrap_or_default();
        let re = Regex::new(r"^AUD-\d{8}-\d{2}$").unwrap();
        if !re.is_match(id) {
            report
                .errors
                .push("Audit id must look like AUD-YYYYMMDD-##".to_string());
        }
        let scope = doc.get("target").or_else(|| doc.get("scope"));
        if let Some(targets) = scope.and_then(|v| v.as_array()) {
            for t in targets {
                if let Some(value) = t.as_str() {
                    if value.starts_with('G') && ctx.get_goal(value).is_none() {
                        report
                            .errors
                            .push(format!("Audit target goal {} missing", value));
                    } else if value.starts_with('D') && ctx.get_decision(value).is_none() {
                        report
                            .errors
                            .push(format!("Audit target decision {} missing", value));
                    }
                }
            }
        }
        report
    }

    fn validate_canon(doc: &Value, allowed: &HashSet<String>) -> ValidationReport {
        let mut report = ValidationReport::ok();
        if let Some(canon) = doc.get("canon_refs").and_then(|v| v.as_array()) {
            for entry in canon {
                if let Some(value) = entry.as_str() {
                    if !allowed.contains(&value.to_lowercase()) {
                        report
                            .warnings
                            .push(format!("Canon ref {} not verified", value));
                    }
                }
            }
        }
        report
    }
}
