use anyhow::Result;
use chrono::Local;
use meta_core::GovernanceContext;

pub fn run_today(root: &str, show: bool) -> Result<()> {
    let today = Local::now().naive_local().date();
    let ctx = GovernanceContext::load(root)?;
    let file_path = ctx.ensure_daily_note(today)?;

    if show {
        println!("{}", file_path.display());
    } else {
        // Try to open in $EDITOR
        if let Ok(editor) = std::env::var("EDITOR") {
            std::process::Command::new(editor)
                .arg(&file_path)
                .status()?;
        } else {
            println!("Created/found: {}", file_path.display());
            println!("Set $EDITOR environment variable to open automatically");
        }
    }

    Ok(())
}
