use crate::domain::*;
use crate::errors::{MetaError, Result};
use crate::parser::MarkdownParser;
use std::collections::HashMap;
use std::path::{Path, PathBuf};
use walkdir::WalkDir;

/// Main governance context - loads and manages all governance data
pub struct GovernanceContext {
    pub root: PathBuf,
    pub goals: HashMap<String, Goal>,
    pub decisions: HashMap<String, Decision>,
    pub phases: Vec<Phase>,
}

impl GovernanceContext {
    pub fn load<P: AsRef<Path>>(root: P) -> Result<Self> {
        let root = root.as_ref().to_path_buf();

        if !root.exists() {
            return Err(MetaError::GovernanceFolderNotFound(
                root.to_string_lossy().to_string(),
            ));
        }

        let mut ctx = Self {
            root: root.clone(),
            goals: HashMap::new(),
            decisions: HashMap::new(),
            phases: Vec::new(),
        };

        ctx.load_goals()?;
        ctx.load_decisions()?;

        Ok(ctx)
    }

    fn load_goals(&mut self) -> Result<()> {
        let goals_dir = self.root.join("03_GOALS_EPICS");

        if !goals_dir.exists() {
            return Ok(());
        }

        for entry in WalkDir::new(&goals_dir)
            .max_depth(1)
            .into_iter()
            .filter_map(|e| e.ok())
        {
            let path = entry.path();
            if path.is_file() && path.extension().and_then(|s| s.to_str()) == Some("md") {
                match MarkdownParser::parse_goal(path) {
                    Ok(goal) => {
                        self.goals.insert(goal.goal_id.clone(), goal);
                    }
                    Err(e) => {
                        eprintln!("Warning: Failed to parse goal at {:?}: {}", path, e);
                    }
                }
            }
        }

        Ok(())
    }

    fn load_decisions(&mut self) -> Result<()> {
        let decisions_dir = self.root.join("04_DECISIONS");

        if !decisions_dir.exists() {
            return Ok(());
        }

        for entry in WalkDir::new(&decisions_dir)
            .max_depth(1)
            .into_iter()
            .filter_map(|e| e.ok())
        {
            let path = entry.path();
            if path.is_file() && path.extension().and_then(|s| s.to_str()) == Some("md") {
                match MarkdownParser::parse_decision(path) {
                    Ok(decision) => {
                        self.decisions.insert(decision.decision_id.clone(), decision);
                    }
                    Err(e) => {
                        eprintln!("Warning: Failed to parse decision at {:?}: {}", path, e);
                    }
                }
            }
        }

        Ok(())
    }

    pub fn get_goal(&self, id: &str) -> Option<&Goal> {
        self.goals.get(id)
    }

    pub fn get_decision(&self, id: &str) -> Option<&Decision> {
        self.decisions.get(id)
    }

    pub fn all_goals(&self) -> Vec<&Goal> {
        self.goals.values().collect()
    }

    pub fn all_decisions(&self) -> Vec<&Decision> {
        self.decisions.values().collect()
    }

    pub fn count_files(&self) -> usize {
        self.goals.len() + self.decisions.len()
    }
}
