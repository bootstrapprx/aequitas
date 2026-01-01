// Prevents additional console window on Windows in release mode
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;
mod commands_ai;
mod commands_crud;
mod commands_git;
mod state;
mod watcher_handler;

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
             // PHASE 1 CRITICAL: SurrealDB enabled as read-only cache for dashboard performance
             // See PERSISTENCE_STRATEGY.md and SURREALDB_MIGRATION.md for design
             //
             // Architecture:
             // - Markdown files remain the single source of truth
             // - SurrealDB provides fast, indexed queries for dashboard
             // - GUI writes to markdown → migration updates DB
             // - File watcher keeps DB synchronized

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
                         println!("Running SurrealDB migration...");
                         if let Err(e) = metatheos_core::store::migration::migrate_all(&store, &gov_root).await {
                             eprintln!("Migration failed: {}", e);
                         } else {
                             println!("Migration complete - DB cache ready");
                         }

                         // Set state
                         *state.db.lock().unwrap() = Some(store.clone());
                         println!("SurrealDB initialized and state updated.");

                         // PHASE 2.1: Initialize file watcher for real-time sync
                         println!("Initializing file watcher...");
                         match metatheos_core::FileWatcher::new(&gov_root) {
                             Ok(watcher) => {
                                 *state.watcher.lock().unwrap() = Some(watcher);
                                 println!("File watcher initialized");

                                 // Spawn background task to handle file change events
                                 let handle_clone = handle.clone();
                                 let store_clone = store.clone();
                                 let gov_root_clone = gov_root.clone();

                                 tauri::async_runtime::spawn(async move {
                                     loop {
                                         // Poll for file change events
                                         let event_opt = {
                                             // Scope to ensure mutex guard is dropped before await
                                             if let Some(mut watcher) = handle_clone.state::<AppState>().watcher.lock().unwrap().take() {
                                                 let event = watcher.next_event();
                                                 // Put watcher back immediately
                                                 *handle_clone.state::<AppState>().watcher.lock().unwrap() = Some(watcher);
                                                 event
                                             } else {
                                                 None
                                             }
                                         };

                                         // Handle event if any (mutex is now released)
                                         if let Some(event) = event_opt {
                                             watcher_handler::handle_file_change(
                                                 event,
                                                 store_clone.clone(),
                                                 gov_root_clone.clone(),
                                                 handle_clone.clone(),
                                             ).await;
                                         }

                                         // Sleep to avoid busy-waiting
                                         tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
                                     }
                                 });
                             }
                             Err(e) => eprintln!("Failed to init file watcher: {}", e),
                         }
                     },
                     Err(e) => eprintln!("Failed to init SurrealDB: {}", e),
                 }
             });

             println!("Metatheos GUI started (SurrealDB caching mode + file watcher)");
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
            commands::get_aequitas_dashboard,
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
