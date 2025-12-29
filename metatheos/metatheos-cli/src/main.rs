mod args;
mod commands;
mod output;

use anyhow::Result;
use clap::Parser;
use args::{Cli, Commands};

fn main() -> Result<()> {
    let cli = Cli::parse();

    let exit_code = match cli.command {
        Commands::Scan => {
            commands::run_scan(&cli.root)?;
            0
        }

        Commands::Today { show } => {
            commands::run_today(&cli.root, show)?;
            0
        }

        Commands::Audit { format } => commands::run_audit(&cli.root, &format)?,

        Commands::Goals {
            status,
            active,
            phase,
            tag,
            format,
        } => {
            commands::run_goals(&cli.root, status, active, phase, tag, &format)?;
            0
        }

        Commands::Goal { action } => {
            commands::run_goal(&cli.root, &action)?;
            0
        }

        Commands::Phase { action } => {
            commands::run_phase(&cli.root, &action)?;
            0
        }
    };

    std::process::exit(exit_code);
}
