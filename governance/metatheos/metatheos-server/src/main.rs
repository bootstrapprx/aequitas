use axum::{
    extract::{Path, State},
    response::Json,
    routing::{get, post},
    Router,
};
use metatheos_core::AppState;
use serde_json::{json, Value};
use std::net::SocketAddr;
use std::path::PathBuf;
use std::sync::Arc;
use tower_http::cors::CorsLayer;
use tower_http::trace::TraceLayer;

#[tokio::main]
async fn main() {
    // Initialize tracing
    tracing_subscriber::fmt()
        .with_max_level(tracing::Level::INFO)
        .init();

    tracing::info!("Starting Metatheos Server...");

    // Determine governance root (from env or default)
    let governance_root = std::env::var("AEQUITAS_GOVERNANCE")
        .map(PathBuf::from)
        .unwrap_or_else(|_| PathBuf::from("./governance")); // Default for docker mount

    tracing::info!("Governance Root: {:?}", governance_root);

    // Initialize State (SurrealDB + Core)
    let db_path = governance_root.join(".metatheos.db");
    let store = metatheos_core::store::SurrealStore::init(db_path)
        .await
        .expect("Failed to init SurrealDB");
    
    // Seed/Migrate
    if let Err(e) = metatheos_core::store::migration::migrate_all(&store, &governance_root).await {
        tracing::error!("Migration warnings: {}", e);
    }

    let shared_state = Arc::new(AppState {
        store: Arc::new(store),
        config: metatheos_core::Config::default(),
        root_path: governance_root,
    });

    // Build Router
    let app = Router::new()
        .route("/health", get(health_check))
        .route("/api/invoke/:command", post(handle_invoke))
        .layer(CorsLayer::permissive())
        .layer(TraceLayer::new_for_http())
        .with_state(shared_state);

    // Run Server
    let addr = SocketAddr::from(([0, 0, 0, 0], 3000));
    tracing::info!("listening on {}", addr);
    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}

async fn health_check() -> Json<Value> {
    Json(json!({ "status": "ok", "version": "0.1.0" }))
}

async fn handle_invoke(
    State(state): State<Arc<AppState>>,
    Path(command): Path<String>,
    Json(payload): Json<Value>,
) -> Json<Value> {
    tracing::debug!("Invoke: {} with {:?}", command, payload);

    // ROUTER for Core Commands
    // This maps the string command name to the actual core function
    // In Tauri this is automatic, here we map manually or use a macro
    // For MVP we map key dashboard commands
    
    let result = match command.as_str() {
        "get_today_day" => {
            metatheos_core::api::get_today_day(&state.store).await
                .map(|v| serde_json::to_value(v).unwrap())
        },
        "get_all_phases" => {
             metatheos_core::api::get_all_phases(&state.store).await
                .map(|v| serde_json::to_value(v).unwrap())
        },
        "get_active_phase" => {
             metatheos_core::api::get_active_phase(&state.store, None).await
                .map(|v| serde_json::to_value(v).unwrap())
        },
        // "get_goal_detail" => {
        //      let id = payload.get("goalId").and_then(|v| v.as_str()).unwrap_or("");
        //      metatheos_core::api::get_goal_detail(&state.store, id).await
        //         .map(|v| serde_json::to_value(v).unwrap())
        // },
        // ADD MORE COMMANDS HERE AS NEEDED
        _ => Err(anyhow::anyhow!("Command not found: {}", command)),
    };

    match result {
        Ok(val) => Json(json!({ "status": "ok", "data": val })),
        Err(e) => Json(json!({ "status": "error", "message": e.to_string() })),
    }
}
