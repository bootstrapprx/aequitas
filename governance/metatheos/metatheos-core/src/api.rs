use crate::store::SurrealStore;
use crate::{
    AuditRecord, CanonDoc, Decision, Goal, GoalStatus, Phase, PhaseGoalBreakdown, ProtocolDoc,
};
use serde::{Deserialize, Serialize};
use chrono::NaiveDate;

#[derive(Debug, Serialize, Deserialize)]
pub struct GoalDto {
    pub goal_id: String,
    pub title: String,
    pub status: String,
    pub phase: Option<String>,
    pub level: Option<String>,
    pub owner: Option<String>,
    pub parent_id: Option<String>,
    pub dependencies: Vec<String>,
    pub canon: Vec<String>,
    pub tags: Vec<String>,
    pub updated: Option<String>,
    pub file_path: String,
    pub completion_pct: u8,
}

impl From<&Goal> for GoalDto {
    fn from(goal: &Goal) -> Self {
        let completion_pct = match goal.status {
            GoalStatus::Done | GoalStatus::Archived => 100,
            GoalStatus::Partial => 50,
            _ => 0,
        };
        Self {
            goal_id: goal.goal_id.clone(),
            title: goal.title.clone(),
            status: goal.status.to_string(),
            phase: goal.phase.clone(),
            level: goal.level.clone(),
            owner: goal.owner.clone(),
            parent_id: goal.parent_id.clone(),
            dependencies: goal.dependencies.clone(),
            canon: goal.canon.clone(),
            tags: goal.tags.clone(),
            updated: goal.updated.map(|d| d.to_string()),
            file_path: goal.file_path.to_string_lossy().to_string(),
            completion_pct,
        }
    }
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PhaseDto {
    pub phase_id: String,
    pub title: String,
    pub status: Option<String>,
    pub updated: Option<String>,
}

impl From<&Phase> for PhaseDto {
    fn from(phase: &Phase) -> Self {
        PhaseDto {
            phase_id: phase.phase_id.clone(),
            title: phase.title.clone(),
            status: Some(phase.status.clone()),
            updated: None,
        }
    }
}

// Logic implementations
pub async fn get_all_phases(store: &SurrealStore) -> crate::Result<Vec<PhaseDto>> {
    let phases = store.get_all_phases().await?;
    Ok(phases.iter().map(PhaseDto::from).collect())
}

// More DTOs and logic will be added here

pub async fn resolve_active_phase_db(
    store: &SurrealStore,
    date: Option<NaiveDate>,
) -> crate::Result<Option<crate::Phase>> {
    // 1. Check Day (if provided)
    if let Some(d) = date {
        if let Ok(Some(note)) = store.get_daily_note(d).await {
            if let Some(pid) = &note.phase {
                if let Ok(all_phases) = store.get_all_phases().await {
                    if let Some(p) = all_phases.into_iter().find(|p| &p.phase_id == pid) {
                        return Ok(Some(p));
                    }
                }
            }
        }
    }

    // 2. Check Meta (Global Active Phase)
    if let Ok(Some(active_id)) = store.get_meta("active_phase").await {
        if let Ok(all_phases) = store.get_all_phases().await {
            if let Some(p) = all_phases.into_iter().find(|p| p.phase_id == active_id) {
                return Ok(Some(p));
            }
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

pub async fn get_active_phase(
    store: &SurrealStore,
    date: Option<NaiveDate>,
) -> crate::Result<Option<PhaseDto>> {
    let phase = resolve_active_phase_db(store, date).await?;
    Ok(phase.as_ref().map(PhaseDto::from))
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DayDto {
    pub id: String,
    pub phase_id: String,
    pub day_type: String,
    pub created_at: String,
}

pub async fn get_day(store: &SurrealStore, date: String) -> crate::Result<Option<DayDto>> {
    let day_opt: Option<Day> = store
        .get_db()
        .select(("day", date.as_str()))
        .await
        .map_err(|e| crate::MetaError::StoreError(e.to_string()))?;

    Ok(day_opt.map(|d| DayDto {
        id: d.id,
        phase_id: d.phase_id,
        day_type: d.day_type.as_str().to_string(),
        created_at: d.created_at.to_rfc3339(),
    }))
}

pub async fn get_today_day(store: &SurrealStore) -> crate::Result<Option<DayDto>> {
    let today = Local::now()
        .naive_local()
        .date()
        .format("%Y-%m-%d")
        .to_string();
    get_day(store, today).await
}
