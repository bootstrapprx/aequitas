use clap::{Parser, Subcommand};
use meta_core::GoalStatus;

#[derive(Parser)]
#[command(name = "meta")]
#[command(about = "Aequitas Meta Engine - Governance CLI", long_about = None)]
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
    /// Initialize or open today's daily note
    Today {
        /// Show path instead of opening
        #[arg(long)]
        show: bool,
    },

    /// Validate governance integrity
    Audit {
        /// Output format: markdown, json, table
        #[arg(long, default_value = "markdown")]
        format: String,

        /// Treat warnings as errors
        #[arg(long)]
        strict: bool,
    },

    /// List goals with filtering
    Goals {
        /// Filter by status: active, blocked, completed, archived
        #[arg(long)]
        status: Option<String>,

        /// Filter by phase number
        #[arg(long)]
        phase: Option<u32>,

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
}

#[derive(Subcommand)]
pub enum GoalAction {
    /// Show full goal details
    Show { goal_id: String },

    /// Update goal status
    Set {
        goal_id: String,
        status: String,
    },

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
    GoalStatus::from_str(s)
        .ok_or_else(|| format!("Invalid status: {}. Expected: active, blocked, completed, archived", s))
}
