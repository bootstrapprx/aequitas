use axum::{
    extract::{Path, Query, State},
    http::{HeaderMap, HeaderValue, StatusCode},
    response::{IntoResponse, Json},
    routing::{get, post},
    Router,
};
use metatheos_core::{ApiErrorDto, AppState, AuthStatusDto};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::net::SocketAddr;
use std::path::PathBuf;
use std::sync::Arc;
use tower_http::cors::{Any, CorsLayer};
use tower_http::trace::TraceLayer;

// ============================================================================
// MAIN
// ============================================================================

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
        .unwrap_or_else(|_| PathBuf::from("./governance"));

    tracing::info!("Governance Root: {:?}", governance_root);

    // Initialize State (SurrealDB + Core)
    let db_path = governance_root.join(".metatheos.db");
    let store = metatheos_core::store::SurrealStore::init(db_path.clone())
        .await
        .expect("Failed to init SurrealDB");

    // Log read mode on startup (kill-switch visibility)
    store.log_read_mode().await;

    // Seed/Migrate
    if let Err(e) = metatheos_core::store::migration::migrate_all(&store, &governance_root).await {
        tracing::error!("Migration warnings: {}", e);
    }

    let shared_state = Arc::new(AppState {
        store: Arc::new(store),
        config: metatheos_core::Config::default(),
        root_path: governance_root,
    });

    // CORS configuration for cross-origin UI
    let cors = CorsLayer::new()
        .allow_origin(Any)
        .allow_methods(Any)
        .allow_headers(Any)
        .allow_credentials(false);

    // Build Router with dedicated REST routes
    let app = Router::new()
        // Health & Context
        .route("/health", get(health_check))
        .route("/api/health", get(api_health))
        .route("/api/context/overview", get(context_overview))
        // Phases
        .route("/api/phases", get(list_phases))
        .route("/api/phases/:id", get(get_phase))
        // Goals
        .route("/api/goals", get(list_goals))
        .route("/api/goals/:id", get(get_goal))
        // Days
        .route("/api/day/today", get(get_today))
        .route("/api/day/:date", get(get_day_by_date))
        // Timeline
        .route("/api/timeline", get(get_timeline))
        // Prompts & Audits (read-only)
        .route("/api/prompts", get(list_prompts))
        .route("/api/audits", get(list_audits))
        // Auth (stub)
        .route("/api/auth/login", post(auth_login))
        .route("/api/auth/logout", post(auth_logout))
        .route("/api/auth/me", get(auth_me))
        // Deprecated legacy invoke (kept for backward compat)
        .route("/api/invoke/:command", post(handle_invoke_deprecated))
        .layer(cors)
        .layer(TraceLayer::new_for_http())
        .with_state(shared_state);

    // Run Server
    let addr = SocketAddr::from(([0, 0, 0, 0], 3000));
    tracing::info!("listening on {}", addr);
    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}

// ============================================================================
// HEALTH ENDPOINTS
// ============================================================================

async fn health_check() -> Json<Value> {
    Json(json!({ "status": "ok", "version": "0.2.0" }))
}

async fn api_health(State(state): State<Arc<AppState>>) -> Json<Value> {
    let read_mode = state.store.get_read_mode().await;
    let db_healthy = state.store.get_meta("schema_version").await.is_ok();
    
    Json(json!({
        "status": "ok",
        "version": "0.2.0",
        "db_healthy": db_healthy,
        "read_mode": read_mode.as_str()
    }))
}

// ============================================================================
// CONTEXT OVERVIEW
// ============================================================================

async fn context_overview(State(state): State<Arc<AppState>>) -> Result<Json<Value>, AppError> {
    let db_path = state.root_path.join(".metatheos.db").to_string_lossy().to_string();
    
    let overview = metatheos_core::api::get_context_overview(&state.store, Some(db_path)).await
        .map_err(|e| AppError::Database(e.to_string()))?;
    
    Ok(Json(serde_json::to_value(overview).unwrap()))
}

// ============================================================================
// PHASE ENDPOINTS
// ============================================================================

async fn list_phases(State(state): State<Arc<AppState>>) -> Result<Json<Value>, AppError> {
    let phases = metatheos_core::api::get_all_phases(&state.store).await
        .map_err(|e| AppError::Database(e.to_string()))?;
    
    Ok(Json(json!({ "data": phases })))
}

async fn get_phase(
    State(state): State<Arc<AppState>>,
    Path(id): Path<String>,
) -> Result<Json<Value>, AppError> {
    let phase = metatheos_core::api::get_phase_by_id(&state.store, &id).await
        .map_err(|e| AppError::Database(e.to_string()))?;
    
    match phase {
        Some(p) => Ok(Json(json!({ "data": p }))),
        None => Err(AppError::NotFound("Phase".to_string())),
    }
}

// ============================================================================
// GOAL ENDPOINTS
// ============================================================================

#[derive(Debug, Deserialize)]
struct GoalsQuery {
    phase_id: Option<String>,
}

async fn list_goals(
    State(state): State<Arc<AppState>>,
    Query(params): Query<GoalsQuery>,
) -> Result<Json<Value>, AppError> {
    let goals = match params.phase_id {
        Some(pid) => metatheos_core::api::get_goals_by_phase(&state.store, &pid).await,
        None => metatheos_core::api::get_all_goals(&state.store).await,
    }.map_err(|e| AppError::Database(e.to_string()))?;
    
    Ok(Json(json!({ "data": goals })))
}

async fn get_goal(
    State(state): State<Arc<AppState>>,
    Path(id): Path<String>,
) -> Result<Json<Value>, AppError> {
    let goal = metatheos_core::api::get_goal_by_id(&state.store, &id).await
        .map_err(|e| AppError::Database(e.to_string()))?;
    
    match goal {
        Some(g) => Ok(Json(json!({ "data": g }))),
        None => Err(AppError::NotFound("Goal".to_string())),
    }
}

// ============================================================================
// DAY ENDPOINTS
// ============================================================================

async fn get_today(State(state): State<Arc<AppState>>) -> Result<Json<Value>, AppError> {
    let day = metatheos_core::api::get_today_day(&state.store).await
        .map_err(|e| AppError::Database(e.to_string()))?;
    
    Ok(Json(json!({ "data": day })))
}

async fn get_day_by_date(
    State(state): State<Arc<AppState>>,
    Path(date): Path<String>,
) -> Result<Json<Value>, AppError> {
    let day = metatheos_core::api::get_day(&state.store, &date).await
        .map_err(|e| AppError::Database(e.to_string()))?;
    
    Ok(Json(json!({ "data": day })))
}

// ============================================================================
// TIMELINE ENDPOINTS
// ============================================================================

#[derive(Debug, Deserialize)]
struct TimelineQuery {
    limit: Option<usize>,
    phase_id: Option<String>,
    goal_id: Option<String>,
}

async fn get_timeline(
    State(state): State<Arc<AppState>>,
    Query(params): Query<TimelineQuery>,
) -> Result<Json<Value>, AppError> {
    let limit = params.limit.unwrap_or(50);
    let phase_id = params.phase_id.as_deref();
    let goal_id = params.goal_id.as_deref();
    
    let timeline = metatheos_core::api::get_timeline(&state.store, limit, phase_id, goal_id).await
        .map_err(|e| AppError::Database(e.to_string()))?;
    
    Ok(Json(json!({ "data": timeline })))
}

// ============================================================================
// PROMPTS & AUDITS
// ============================================================================

async fn list_prompts(State(state): State<Arc<AppState>>) -> Result<Json<Value>, AppError> {
    let prompts = metatheos_core::api::get_all_prompts(&state.store).await
        .map_err(|e| AppError::Database(e.to_string()))?;
    
    Ok(Json(json!({ "data": prompts })))
}

async fn list_audits(State(state): State<Arc<AppState>>) -> Result<Json<Value>, AppError> {
    let audits = metatheos_core::api::get_all_audits(&state.store).await
        .map_err(|e| AppError::Database(e.to_string()))?;
    
    Ok(Json(json!({ "data": audits })))
}

// ============================================================================
// AUTH ENDPOINTS (Stub with env-based admin password)
// ============================================================================

#[derive(Debug, Deserialize)]
struct LoginRequest {
    password: String,
}

#[derive(Debug, Serialize)]
struct LoginResponse {
    token: String,
}

async fn auth_login(Json(payload): Json<LoginRequest>) -> Result<Json<Value>, AppError> {
    let admin_password = std::env::var("METATHEOS_ADMIN_PASSWORD")
        .unwrap_or_else(|_| "admin".to_string());
    
    if payload.password == admin_password {
        // Simple token (in production, use JWT)
        let token = format!("meta-session-{}", uuid::Uuid::new_v4());
        Ok(Json(json!({ "status": "ok", "token": token })))
    } else {
        Err(AppError::Unauthorized)
    }
}

async fn auth_logout() -> Json<Value> {
    Json(json!({ "status": "ok", "message": "Logged out" }))
}

async fn auth_me() -> Json<Value> {
    // Stub: always returns admin (in production, validate session token)
    let status = AuthStatusDto::admin();
    Json(serde_json::to_value(status).unwrap())
}

// ============================================================================
// DEPRECATED INVOKE ENDPOINT
// ============================================================================

async fn handle_invoke_deprecated(
    State(state): State<Arc<AppState>>,
    Path(command): Path<String>,
    Json(payload): Json<Value>,
) -> impl IntoResponse {
    // Log deprecation warning
    tracing::warn!(
        "DEPRECATED: /api/invoke/{} called. Use dedicated REST endpoints instead.",
        command
    );

    // Execute command (legacy compatibility)
    let result = match command.as_str() {
        "get_today_day" => {
            metatheos_core::api::get_today_day(&state.store)
                .await
                .map(|v| serde_json::to_value(v).unwrap())
        }
        "get_all_phases" => {
            metatheos_core::api::get_all_phases(&state.store)
                .await
                .map(|v| serde_json::to_value(v).unwrap())
        }
        "get_active_phase" => {
            metatheos_core::api::get_active_phase(&state.store, None)
                .await
                .map(|v| serde_json::to_value(v).unwrap())
        }
        _ => Err(metatheos_core::MetaError::SystemError(format!(
            "Command not found: {}",
            command
        ))),
    };

    // Build response with deprecation header
    let mut headers = HeaderMap::new();
    headers.insert(
        "X-Metatheos-Deprecated",
        HeaderValue::from_static("invoke-api"),
    );

    let body = match result {
        Ok(val) => json!({ "status": "ok", "data": val }),
        Err(e) => json!({ "status": "error", "message": e.to_string() }),
    };

    (headers, Json(body))
}

// ============================================================================
// ERROR HANDLING
// ============================================================================

enum AppError {
    Database(String),
    NotFound(String),
    Unauthorized,
}

impl IntoResponse for AppError {
    fn into_response(self) -> axum::response::Response {
        let (status, error) = match self {
            AppError::Database(msg) => (
                StatusCode::INTERNAL_SERVER_ERROR,
                ApiErrorDto::database_error(msg),
            ),
            AppError::NotFound(entity) => (
                StatusCode::NOT_FOUND,
                ApiErrorDto::not_found(entity),
            ),
            AppError::Unauthorized => (
                StatusCode::UNAUTHORIZED,
                ApiErrorDto::unauthorized(),
            ),
        };

        let body = Json(serde_json::to_value(error).unwrap());
        (status, body).into_response()
    }
}
