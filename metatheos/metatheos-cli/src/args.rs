use clap::{Parser, Subcommand};
use metatheos_core::GoalStatus;

#[derive(Parser)]
#[command(name = "metatheos")]
#[command(about = "Metatheos - Aequitas Governance Engine", long_about = None)]
#[command(version)]
pub struct Cli {
    /// Path to governance root folder
    #[arg(long, default_value = "./governance", global = true)]
    pub root: String,

    /// Enable verbose output
    #[arg(short, long, global = true)]
    pub verbose: bool,

    /// Suppress non-error output
    #[arg(short, long, global = true)]
    pub quiet: bool,

    #[command(subcommand)]
    pub command: Commands,
}

#[derive(Subcommand)]
pub enum Commands {
    /// Summarize governance state
    Scan,

    /// Initialize or open today's daily note
    Today {
        /// Show path instead of opening
        #[arg(long)]
        show: bool,
    },

    /// List governance audits
    Audit {
        /// Output format: markdown, json, table
        #[arg(long, default_value = "table")]
        format: String,
    },

    /// List goals with filtering
    Goals {
        /// Filter by status: planned, active, blocked, partial, done
        #[arg(long)]
        status: Option<String>,

        /// Quick filter for active goals
        #[arg(long, conflicts_with = "status")]
        active: bool,

        /// Filter by phase number
        #[arg(long)]
        phase: Option<String>,

        /// Filter by tag
        #[arg(long)]
        tag: Option<String>,

        /// Output format: markdown, json, table
        #[arg(long, default_value = "table")]
        format: String,
    },

    /// Operate on individual goals
    Goal {
        #[command(subcommand)]
        action: GoalAction,
    },

    /// Phase information and management
    Phase {
        #[command(subcommand)]
        action: PhaseAction,
    },

    /// Migrate markdown files to SurrealDB cache
    Migrate,
}

#[derive(Subcommand)]
pub enum GoalAction {
    /// Show full goal details
    Show { goal_id: String },

    /// Update goal status
    Set { goal_id: String, status: String },

    /// Show dependency tree
    Deps { goal_id: String },
}

#[derive(Subcommand)]
pub enum PhaseAction {
    /// Show current active phase
    Current,

    /// List all phases
    List,

    /// Validate phase coherence
    Validate,
}

pub fn parse_goal_status(s: &str) -> Result<GoalStatus, String> {
    match s.to_lowercase().as_str() {
        "planned" => Ok(GoalStatus::Planned),
        "active" => Ok(GoalStatus::Active),
        "blocked" => Ok(GoalStatus::Blocked),
        "partial" => Ok(GoalStatus::Partial),
        "done" | "completed" => Ok(GoalStatus::Done),
        "archived" => Ok(GoalStatus::Archived),
        other => Ok(GoalStatus::Unknown(other.to_string())),
    }
}
