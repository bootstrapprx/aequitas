use crate::store::SurrealStore;
use crate::{Goal, Result, WorkItem};

/// Compute task completion for a goal by loading work items (no new schema)
pub async fn get_goal_task_completion(
    store: &SurrealStore,
    goal_id: &str,
) -> Result<(usize, usize)> {
    let items: Vec<WorkItem> = store.get_work_items_by_goal(goal_id).await?;
    let total_tasks = items
        .iter()
        .filter(|i| matches!(i.level, crate::WorkItemLevel::Task))
        .count();
    let done_tasks = items
        .iter()
        .filter(|i| {
            matches!(i.level, crate::WorkItemLevel::Task)
                && matches!(i.status, crate::WorkItemStatus::Done)
        })
        .count();
    Ok((total_tasks, done_tasks))
}

/// Phase progress based on goals in that phase
pub async fn get_phase_progress(store: &SurrealStore, phase_id: &str) -> Result<(usize, usize)> {
    let mut resp = store
        .db
        .query("SELECT * FROM goal WHERE phase_id = $pid")
        .bind(("pid", phase_id.to_string()))
        .await
        .map_err(|e| crate::errors::MetaError::SystemError(format!("DB Query Error: {}", e)))?;
    let goals: Vec<Goal> = resp.take(0).map_err(|e| {
        crate::errors::MetaError::SystemError(format!("DB Deserialization Error: {}", e))
    })?;
    let total = goals.len();
    let done = goals
        .iter()
        .filter(|g| {
            matches!(
                g.status,
                crate::GoalStatus::Done | crate::GoalStatus::Archived
            )
        })
        .count();
    Ok((total, done))
}

/// Required day goals status snapshot (required_count, done_required)
pub async fn get_day_required_goal_status(
    store: &SurrealStore,
    day_id: &str,
) -> Result<(usize, usize)> {
    let mut resp = store
        .db
        .query("SELECT goal_id, required FROM day_goal WHERE day_id = $day")
        .bind(("day", day_id.to_string()))
        .await
        .map_err(|e| crate::errors::MetaError::SystemError(format!("DB Query Error: {}", e)))?;

    #[derive(serde::Deserialize)]
    struct DayGoalRow {
        goal_id: String,
        required: bool,
    }
    let rows: Vec<DayGoalRow> = resp.take(0).map_err(|e| {
        crate::errors::MetaError::SystemError(format!("DB Deserialization Error: {}", e))
    })?;

    let required_rows: Vec<DayGoalRow> = rows.into_iter().filter(|r| r.required).collect();
    let required_count = required_rows.len();
    let mut done_count = 0usize;
    for row in required_rows {
        if let Ok(Some(goal)) = store
            .get_db()
            .select::<Option<Goal>>(("goal", row.goal_id.as_str()))
            .await
        {
            if matches!(
                goal.status,
                crate::GoalStatus::Done | crate::GoalStatus::Archived
            ) {
                done_count += 1;
            }
        }
    }

    Ok((required_count, done_count))
}
