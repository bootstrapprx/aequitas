// Prevents additional console window on Windows in release mode
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;
mod commands_ai;
mod commands_crud;
mod commands_git;
mod state;

use state::AppState;
use std::path::PathBuf;
use tauri::Manager;

fn main() {
    // Default governance root - absolute path to Aequitas governance folder
    let governance_root = std::env::var("AEQUITAS_GOVERNANCE")
        .map(PathBuf::from)
        .unwrap_or_else(|_| {
            // Default to governance folder in Aequitas project
            #[cfg(target_os = "linux")]
            let home = std::path::PathBuf::from(std::env::var("HOME").unwrap_or_else(|_| "/home/actpm".to_string()));
            #[cfg(not(target_os = "linux"))]
             let home = std::path::PathBuf::from("/"); // Fallback for safety

            home.join("Documents/workfolder/aequitas/governance")
        });
    
    // Assume repo root is the parent of governance root
    let repo_root = governance_root.parent().unwrap_or(&governance_root).to_path_buf();

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(AppState::new(governance_root.clone(), repo_root))
        .setup(move |app| {
             let handle = app.handle().clone();
             let gov_root = governance_root.clone();
             
             tauri::async_runtime::spawn(async move {
                 let state = handle.state::<AppState>();
                 let db_path = gov_root.join(".metatheos.db"); // Embedded DB folder
                 println!("Initializing SurrealDB at {:?}", db_path);
                 match metatheos_core::store::SurrealStore::init(db_path).await {
                     Ok(store) => {
                         let store = std::sync::Arc::new(store);
                         
                         // Run Migration
                         if let Err(e) = metatheos_core::store::migration::migrate_all(&store, &gov_root).await {
                             eprintln!("Migration failed: {}", e);
                         }
                         
                         // Set state
                         *state.db.lock().unwrap() = Some(store);
                         println!("SurrealDB initialized and state updated.");
                     },
                     Err(e) => eprintln!("Failed to init SurrealDB: {}", e),
                 }
             });
             Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            // Read commands
            commands::get_all_goals,
            commands::get_enriched_goals,
            commands::get_all_audits,
            commands::get_all_prompts,
            commands::get_enriched_audits,
            commands::get_enriched_prompts,
            commands::check_governance_layout,
            commands::get_governance_tree,
            commands::get_file_content,
            commands::get_file_backlinks,
            commands::safe_write_file,
            commands::get_goals_by_status,
            commands::get_goals_by_phase,
            commands::get_dashboard_data,
            commands::get_daily_context,
            commands::update_goal_status,
            commands::create_daily_note,
            commands::list_audits,
            commands::set_daily_mode,
            commands::list_audits,
            commands::set_daily_mode,
            commands::get_daily_note, // It is now async, still valid handler
            commands::update_daily_note,
            // AI commands
            commands_ai::ai_check_config,
            commands_ai::ai_ask,
            commands_ai::ai_suggest_status,
            commands_ai::ai_get_examples,
            commands_ai::get_context_clipboard_payload,
            commands_ai::ollama_reason,
            // CRUD commands (Phase 5)
            commands_crud::create_goal,
            commands_crud::update_goal,
            commands_crud::delete_goal,
            commands_crud::create_phase,
            commands_crud::update_phase,
            commands_crud::set_active_phase,
            commands_crud::delete_daily_note,
            commands_crud::write_daily_note, // Async now
            // Audit & Prompt commands (Phase 6A)
            commands_crud::create_audit,
            commands_crud::update_audit,
            commands_crud::delete_audit,
            commands_crud::create_prompt,
            commands_crud::update_prompt,
            commands_crud::delete_prompt,
            // Git commands (Phase 3)
            commands_git::get_governance_git_status,
            commands_git::commit_governance_changes,
            commands_git::get_file_history,
            commands_git::get_last_governance_commit,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
