// Prevents additional console window on Windows in release mode
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;
mod state;

use state::AppState;
use std::path::PathBuf;

fn main() {
    // Default governance root - absolute path to Aequitas governance folder
    let governance_root = std::env::var("AEQUITAS_GOVERNANCE")
        .map(PathBuf::from)
        .unwrap_or_else(|_| {
            // Default to governance folder in Aequitas project
            let home = std::env::var("HOME").expect("HOME not set");
            PathBuf::from(home)
                .join("Documents/workfolder/aequitas/governance")
        });

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(AppState::new(governance_root))
        .invoke_handler(tauri::generate_handler![
            commands::get_all_goals,
            commands::get_goals_by_status,
            commands::get_goals_by_phase,
            commands::get_dashboard_data,
            commands::update_goal_status,
            commands::create_daily_note,
            commands::list_audits,
            commands::set_daily_mode,
            commands::get_daily_note,
            commands::update_daily_note,
            commands::list_daily_notes,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
