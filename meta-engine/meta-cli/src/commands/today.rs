use anyhow::Result;
use chrono::Local;
use std::fs;
use std::path::Path;

pub fn run_today(root: &str, show: bool) -> Result<()> {
    let today = Local::now().naive_local().date();
    let filename = format!("{}.md", today.format("%Y-%m-%d"));
    let daily_dir = Path::new(root).join("01_DAILY");
    let file_path = daily_dir.join(&filename);

    // Create directory if it doesn't exist
    if !daily_dir.exists() {
        fs::create_dir_all(&daily_dir)?;
    }

    // Create file if it doesn't exist
    if !file_path.exists() {
        let template = format!(
            r#"---
date: {}
phase:
---

# Daily Log — {}

## Goals Worked
-

## Decisions Made
-

## Divergences Noted
-
"#,
            today.format("%Y-%m-%d"),
            today.format("%Y-%m-%d")
        );

        fs::write(&file_path, template)?;
    }

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
