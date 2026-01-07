// Prevents additional console window on Windows in release mode
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;
mod commands_ai;
mod commands_crud;
mod commands_git;
mod roadmap_loader;
mod state;

use state::AppState;
use std::path::PathBuf;
use tauri::{Emitter, Manager};

fn main() {
    // Default governance root - absolute path to Aequitas governance folder
    let governance_root = std::env::var("AEQUITAS_GOVERNANCE")
        .map(PathBuf::from)
        .unwrap_or_else(|_| {
            // Default to governance folder in Aequitas project
            #[cfg(target_os = "linux")]
            let home = std::path::PathBuf::from(
                std::env::var("HOME").unwrap_or_else(|_| "/home/actpm".to_string()),
            );
            #[cfg(not(target_os = "linux"))]
            let home = std::path::PathBuf::from("/"); // Fallback for safety

            home.join("Documents/workfolder/aequitas/governance")
        });

    // Assume repo root is the parent of governance root
    let repo_root = governance_root
        .parent()
        .unwrap_or(&governance_root)
        .to_path_buf();

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
                        if let Err(e) =
                            metatheos_core::store::migration::migrate_all(&store, &gov_root).await
                        {
                            eprintln!("Migration failed: {}", e);
                        } else {
                            println!("Migration complete - DB cache ready");
                        }

                        // Seed default roadmap if phase table is empty
                        println!("Checking if default roadmap needs seeding...");
                        match store.get_all_phases().await {
                            Ok(phases) if phases.is_empty() => {
                                println!("Phase table is empty - seeding default roadmap");
                                if let Err(e) = commands::seed_default_roadmap(&store).await {
                                    eprintln!("Failed to seed default roadmap: {}", e);
                                }
                            }
                            Ok(phases) => {
                                println!("Found {} existing phases - skipping seed", phases.len());
                            }
                            Err(e) => {
                                eprintln!("Failed to check phases: {} - attempting seed anyway", e);
                                if let Err(e) = commands::seed_default_roadmap(&store).await {
                                    eprintln!("Failed to seed default roadmap: {}", e);
                                }
                            }
                        }

                        // Set state
                        *state.db.lock().unwrap() = Some(store.clone());
                        println!("SurrealDB initialized and state updated.");

                        // PHASE 2.1: Initialize file watcher for real-time sync
                        println!("Initializing file watcher...");
                        // PHASE 2.1: Initialize file watcher for real-time sync
                        println!("Initializing file watcher service...");

                        // Initialize WatcherService
                        match metatheos_core::WatcherService::new(&gov_root, store.clone()) {
                            Ok((service, watcher, mut rx)) => {
                                println!("WatcherService initialized");

                                // Spawn the service (handles DB updates)
                                tauri::async_runtime::spawn(async move {
                                    service.run(watcher).await;
                                });

                                // Spawn the event listener (handles UI notifications)
                                let handle_clone = handle.clone();
                                tauri::async_runtime::spawn(async move {
                                    loop {
                                        match rx.recv().await {
                                            Ok(event) => {
                                                println!(
                                                    "Watcher Event: {} {} ({})",
                                                    event.entity_type, event.id, event.operation
                                                );

                                                // Map to frontend event names (lowercase)
                                                let type_str = event.entity_type.to_lowercase();

                                                // Emit specific changed event (e.g., "goal_changed")
                                                let _ = handle_clone.emit(
                                                    &format!("{}_changed", type_str),
                                                    &event.id,
                                                );

                                                // Emit general governance_changed
                                                let _ = handle_clone
                                                    .emit("governance_changed", &event.id);
                                            }
                                            Err(
                                                tokio::sync::broadcast::error::RecvError::Lagged(n),
                                            ) => {
                                                println!("Watcher event lag: skipped {} events", n);
                                            }
                                            Err(
                                                tokio::sync::broadcast::error::RecvError::Closed,
                                            ) => {
                                                break;
                                            }
                                        }
                                    }
                                });
                            }
                            Err(e) => eprintln!("Failed to init watcher service: {}", e),
                        }
                    }
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
            commands::get_all_phases,
            commands::get_active_phase,
            commands::set_active_phase_db,
            commands::diagnose_store_state,
            commands::get_dashboard_data,
            commands::get_aequitas_dashboard,
            commands::get_daily_context,
            commands::update_goal_status,
            commands::create_daily_note,
            commands::list_audits,
            commands::set_daily_mode,
            commands::begin_day,
            commands::get_daily_note, // It is now async, still valid handler
            commands::update_daily_note,
            commands::get_ai_context,
            // Work Item Commands (Phase 4)
            commands::get_goal_detail,
            commands::create_work_item,
            commands::update_work_item,
            commands::set_work_item_status,
            commands::migrate_legacy_work_items,
            commands::seed_default_phase_db,
            commands::add_work_item,
            commands::get_work_items,
            commands::toggle_work_item,
            // Annotation Commands (Phase 5)
            commands::add_annotation,
            commands::get_annotations,
            commands::delete_annotation,
            // Event Retrieval Commands (Phase 5B)
            commands::get_recent_events,
            commands::get_events_by_entity,
            commands::get_actionable_events,
            commands::get_event_stats,
            commands::run_consequence_scan,
            commands::ingest_roadmap,
            commands::load_roadmap_from_file,
            commands::ingest_roadmap_from_file,
            commands::execute_shell_command,
            // Timeline Commands (Phase 5) - Read-only observational surface
            commands::get_timeline_for_day,
            commands::get_timeline_for_goal,
            commands::get_timeline_for_work_item,
            commands::get_timeline_for_phase,
            // Day Wizard Commands (DB-First)
            commands::get_today_day,
            commands::get_day,
            commands::create_day,
            commands::get_day_context,
            commands::get_available_goals_for_day,
            // AI commands
            commands_ai::ai_check_config,
            commands_ai::ai_ask,
            commands_ai::ai_suggest_status,
            commands_ai::ai_get_examples,
            commands_ai::get_context_clipboard_payload,
            commands_ai::ollama_reason,
            commands_ai::ai_assist_draft_tasks,
            commands_ai::ai_assist_refine,
            commands_ai::ai_assist_summarize,
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
