// Prevents additional console window on Windows in release mode
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;
mod state;

use state::AppState;
use std::path::PathBuf;

fn main() {
    // Default governance root - can be configured later
    let governance_root = std::env::var("AEQUITAS_GOVERNANCE")
        .map(PathBuf::from)
        .unwrap_or_else(|_| PathBuf::from("../../governance"));

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(AppState::new(governance_root))
        .invoke_handler(tauri::generate_handler![
            commands::get_all_goals,
            commands::get_goals_by_status,
            commands::get_goals_by_phase,
            commands::run_audit,
            commands::get_current_phase,
            commands::get_dashboard_data,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
