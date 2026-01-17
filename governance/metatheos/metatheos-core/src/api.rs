//! API Layer - Maps domain data to DTOs for UI consumption
//!
//! This module provides the bridge between SurrealStore and UI endpoints.
//! All functions return DTO types from the dto module.

use crate::dto::{
    AuditDto, ContextOverviewDto, CountsDto, DayDto, DbStatusDto, GoalDto, PhaseDto,
    PromptDto, TimelineItemDto,
};
use crate::store::SurrealStore;
use chrono::{Local, NaiveDate};

// ============================================================================
// PHASE FUNCTIONS
// ============================================================================

/// Get all phases as DTOs
pub async fn get_all_phases(store: &SurrealStore) -> crate::Result<Vec<PhaseDto>> {
    let phases = store.get_all_phases().await?;
    Ok(phases.iter().map(PhaseDto::from).collect())
}

/// Get single phase by ID
pub async fn get_phase_by_id(store: &SurrealStore, phase_id: &str) -> crate::Result<Option<PhaseDto>> {
    let phase = store.get_phase_by_id(phase_id).await?;
    Ok(phase.as_ref().map(PhaseDto::from))
}

/// Resolve active phase from DB (checks daily note, meta, or status fallback)
pub async fn resolve_active_phase_db(
    store: &SurrealStore,
    date: Option<NaiveDate>,
) -> crate::Result<Option<crate::Phase>> {
    // 1. Check Day (if provided)
    if let Some(d) = date {
        if let Ok(Some(note)) = store.get_daily_note(d).await {
            if let Some(pid) = &note.phase {
                if let Ok(Some(p)) = store.get_phase_by_id(pid).await {
                    return Ok(Some(p));
                }
            }
        }
    }

    // 2. Check Meta (Global Active Phase)
    if let Ok(Some(active_id)) = store.get_meta("active_phase").await {
        if let Ok(Some(p)) = store.get_phase_by_id(&active_id).await {
            return Ok(Some(p));
        }
    }

    // 3. Fallback: First Active Phase
    if let Ok(all_phases) = store.get_all_phases().await {
        if let Some(p) = all_phases
            .into_iter()
            .find(|p| p.status.eq_ignore_ascii_case("active"))
        {
            return Ok(Some(p));
        }
    }

    Ok(None)
}

/// Get active phase as DTO
pub async fn get_active_phase(
    store: &SurrealStore,
    date: Option<NaiveDate>,
) -> crate::Result<Option<PhaseDto>> {
    let phase = resolve_active_phase_db(store, date).await?;
    Ok(phase.as_ref().map(PhaseDto::from))
}

// ============================================================================
// GOAL FUNCTIONS
// ============================================================================

/// Get all goals as DTOs
pub async fn get_all_goals(store: &SurrealStore) -> crate::Result<Vec<GoalDto>> {
    let goals = store.get_all_goals().await?;
    Ok(goals.iter().map(GoalDto::from).collect())
}

/// Get goals by phase ID
pub async fn get_goals_by_phase(store: &SurrealStore, phase_id: &str) -> crate::Result<Vec<GoalDto>> {
    let goals = store.get_goals_by_phase(phase_id).await?;
    Ok(goals.iter().map(GoalDto::from).collect())
}

/// Get single goal by ID
pub async fn get_goal_by_id(store: &SurrealStore, goal_id: &str) -> crate::Result<Option<GoalDto>> {
    let goal = store.get_goal_by_id(goal_id).await?;
    Ok(goal.as_ref().map(GoalDto::from))
}

// ============================================================================
// DAY FUNCTIONS
// ============================================================================

/// Get day by date string (YYYY-MM-DD)
pub async fn get_day(store: &SurrealStore, date: &str) -> crate::Result<Option<DayDto>> {
    let day = store.get_day(date).await?;
    Ok(day.as_ref().map(DayDto::from))
}

/// Get today's day record
pub async fn get_today_day(store: &SurrealStore) -> crate::Result<Option<DayDto>> {
    let today = Local::now().format("%Y-%m-%d").to_string();
    get_day(store, &today).await
}

// ============================================================================
// AUDIT FUNCTIONS
// ============================================================================

/// Get all audits as DTOs
pub async fn get_all_audits(store: &SurrealStore) -> crate::Result<Vec<AuditDto>> {
    let audits = store.get_all_audits().await?;
    Ok(audits.iter().map(AuditDto::from).collect())
}

// ============================================================================
// PROMPT FUNCTIONS
// ============================================================================

/// Get all prompts as DTOs
pub async fn get_all_prompts(store: &SurrealStore) -> crate::Result<Vec<PromptDto>> {
    let prompts = store.get_all_prompts().await?;
    Ok(prompts.iter().map(PromptDto::from).collect())
}

// ============================================================================
// TIMELINE FUNCTIONS
// ============================================================================

/// Get timeline items (merged events + annotations) with stable sort
/// 
/// Sort order: ts DESC, then kind (event before annotation), then id
/// This prevents "timeline flicker" in React due to unstable ordering.
pub async fn get_timeline(
    store: &SurrealStore,
    limit: usize,
    phase_id: Option<&str>,
    goal_id: Option<&str>,
) -> crate::Result<Vec<TimelineItemDto>> {
    // Fetch events and annotations
    let events = store.get_recent_events(limit, phase_id, goal_id).await?;
    let annotations = store.get_all_annotations_filtered(limit, phase_id, goal_id).await?;

    // Convert to timeline items
    let mut items: Vec<TimelineItemDto> = Vec::with_capacity(events.len() + annotations.len());

    for event in &events {
        items.push(TimelineItemDto::from_event(event));
    }

    for annotation in &annotations {
        items.push(TimelineItemDto::from_annotation(annotation));
    }

    // Stable sort: ts DESC, kind ASC, id ASC
    items.sort_by(|a, b| {
        // Primary: timestamp descending
        match b.ts.cmp(&a.ts) {
            std::cmp::Ordering::Equal => {
                // Secondary: kind (event=0 before annotation=1)
                let kind_a = match a.kind { crate::dto::TimelineKind::Event => 0, crate::dto::TimelineKind::Annotation => 1 };
                let kind_b = match b.kind { crate::dto::TimelineKind::Event => 0, crate::dto::TimelineKind::Annotation => 1 };
                match kind_a.cmp(&kind_b) {
                    std::cmp::Ordering::Equal => {
                        // Tertiary: id ascending
                        a.id.cmp(&b.id)
                    },
                    other => other,
                }
            },
            other => other,
        }
    });

    // Limit final results
    items.truncate(limit);

    Ok(items)
}

// ============================================================================
// CONTEXT OVERVIEW
// ============================================================================

/// Get context overview for dashboard
/// 
/// Returns active phase, current day, counts, and DB health.
/// On partial failures, returns degraded health with available data.
pub async fn get_context_overview(
    store: &SurrealStore,
    db_path: Option<String>,
) -> crate::Result<ContextOverviewDto> {
    // Get read mode
    let read_mode = store.get_read_mode().await;

    // Track health
    let mut healthy = true;

    // Get active phase (graceful degradation)
    let active_phase = match get_active_phase(store, None).await {
        Ok(p) => p,
        Err(_) => {
            healthy = false;
            None
        }
    };

    // Get current day (graceful degradation)
    let current_day = match get_today_day(store).await {
        Ok(d) => d,
        Err(_) => {
            healthy = false;
            None
        }
    };

    // Get counts (graceful degradation - return 0 on error)
    let phases_count = store.get_all_phases().await.map(|v| v.len()).unwrap_or(0);
    let goals_count = store.get_all_goals().await.map(|v| v.len()).unwrap_or(0);
    let work_items_count = store.count_work_items().await.unwrap_or(0);
    let events_count = store.count_events().await.unwrap_or(0);
    let annotations_count = store.count_annotations().await.unwrap_or(0);

    Ok(ContextOverviewDto {
        active_phase,
        current_day,
        counts: CountsDto {
            phases: phases_count,
            goals: goals_count,
            work_items: work_items_count,
            events: events_count,
            annotations: annotations_count,
        },
        db: DbStatusDto {
            path: db_path,
            mode: read_mode.to_string(),
            healthy,
        },
    })
}
