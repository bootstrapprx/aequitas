use std::sync::Arc;

use crate::store::{queries, SurrealStore};
use crate::{Event, EventAction, Result, WorkItemLevel};
use serde_json::json;

pub struct ConsequenceEngine {
    pub store: Arc<SurrealStore>,
}

impl ConsequenceEngine {
    pub async fn on_work_item_completed(&self, work_item_id: &str) -> Result<()> {
        // Fetch the item to find its goal
        let item = self
            .store
            .get_db()
            .select::<Option<crate::WorkItem>>(("work_item", work_item_id))
            .await
            .map_err(|e| crate::errors::MetaError::SystemError(format!("DB Query Error: {}", e)))?
            .ok_or_else(|| {
                crate::errors::MetaError::ValidationError("work_item not found".into())
            })?;

        if !matches!(item.level, WorkItemLevel::Task) {
            return Ok(()); // Only cascade on tasks
        }

        let (total, done) = queries::get_goal_task_completion(&self.store, &item.goal_id).await?;
        if total > 0 && done == total {
            let event = Event::new(
                "goal",
                &item.goal_id,
                EventAction::Update,
                "system",
                json!({
                    "type": "goal_ready_to_complete",
                    "reason": "all_tasks_done",
                    "total_tasks": total,
                    "done_tasks": done
                }),
            );
            let _ = self.store.log_event(&event).await;
        }
        Ok(())
    }

    pub async fn on_goal_status_changed(&self, goal_id: &str) -> Result<()> {
        // Fetch goal and phase
        let goal = self
            .store
            .get_db()
            .select::<Option<crate::Goal>>(("goal", goal_id))
            .await
            .map_err(|e| crate::errors::MetaError::SystemError(format!("DB Query Error: {}", e)))?
            .ok_or_else(|| crate::errors::MetaError::ValidationError("goal not found".into()))?;

        if let Some(phase_id) = goal.phase.clone() {
            let (total, done) = queries::get_phase_progress(&self.store, &phase_id).await?;
            let event = Event::new(
                "phase",
                &phase_id,
                EventAction::Update,
                "system",
                json!({
                    "type": "phase_progress_updated",
                    "phase_id": phase_id,
                    "total_goals": total,
                    "done_goals": done
                }),
            );
            let _ = self.store.log_event(&event).await;

            if total > 0 && done == total {
                let ready = Event::new(
                    "phase",
                    &phase_id,
                    EventAction::Update,
                    "system",
                    json!({
                        "type": "phase_ready_to_close",
                        "reason": "all_goals_done"
                    }),
                );
                let _ = self.store.log_event(&ready).await;
            }
        }

        Ok(())
    }

    pub async fn on_day_goal_updated(&self, day_id: &str) -> Result<()> {
        let (required, done) = queries::get_day_required_goal_status(&self.store, day_id).await?;
        if required == 0 {
            return Ok(()); // No required goals, nothing to evaluate
        }

        if required == done {
            let event = Event::new(
                "day",
                day_id,
                EventAction::Update,
                "system",
                json!({
                    "type": "day_success",
                    "required_goals": required,
                    "completed_required_goals": done
                }),
            );
            let _ = self.store.log_event(&event).await;
        } else {
            let event = Event::new(
                "day",
                day_id,
                EventAction::Update,
                "system",
                json!({
                    "type": "day_progress",
                    "required_goals": required,
                    "completed_required_goals": done
                }),
            );
            let _ = self.store.log_event(&event).await;
        }
        Ok(())
    }

    /// Proactive scan: Detect blocked goals (dependencies not met)
    pub async fn scan_blocked_goals(&self) -> Result<Vec<String>> {
        let query = "
            SELECT * FROM goal
            WHERE status = 'blocked'
            AND array::len(dependencies) > 0
        ";
        let mut result = self.store.get_db().query(query).await.map_err(|e| {
            crate::errors::MetaError::DatabaseQuery(format!(
                "Blocked goals scan query failed: {}",
                e
            ))
        })?;

        let goals: Vec<crate::Goal> = result.take(0).map_err(|e| {
            crate::errors::MetaError::DatabaseSerialization(format!(
                "Failed to parse blocked goals: {}",
                e
            ))
        })?;

        let mut blocked_ids = Vec::new();
        for goal in goals {
            // Check if any dependencies are still open
            let mut unmet_deps = Vec::new();
            for dep_id in &goal.dependencies {
                let dep: Option<crate::Goal> = self
                    .store
                    .get_db()
                    .select(("goal", dep_id.as_str()))
                    .await
                    .map_err(|e| {
                        crate::errors::MetaError::DatabaseQuery(format!(
                            "Failed to lookup goal dependency {}: {}",
                            dep_id, e
                        ))
                    })?;

                if let Some(d) = dep {
                    if d.status != crate::GoalStatus::Done {
                        unmet_deps.push(dep_id.clone());
                    }
                }
            }

            if !unmet_deps.is_empty() {
                let event = Event::new(
                    "goal",
                    &goal.goal_id,
                    EventAction::Update,
                    "system",
                    json!({
                        "type": "goal_blocked",
                        "reason": "unmet_dependencies",
                        "unmet_dependencies": unmet_deps
                    }),
                );
                let _ = self.store.log_event(&event).await;
                blocked_ids.push(goal.goal_id.clone());
            }
        }
        Ok(blocked_ids)
    }

    /// Proactive scan: Detect stale goals (no activity in N days)
    pub async fn scan_stale_goals(&self, days_threshold: i64) -> Result<Vec<String>> {
        let query = format!(
            "SELECT * FROM goal WHERE status IN ['open', 'partial'] AND created_at < time::now() - {}d",
            days_threshold
        );
        let mut result =
            self.store.get_db().query(&query).await.map_err(|e| {
                crate::errors::MetaError::SystemError(format!("Query error: {}", e))
            })?;

        let goals: Vec<crate::Goal> = result
            .take(0)
            .map_err(|e| crate::errors::MetaError::SystemError(format!("Parse error: {}", e)))?;

        let mut stale_ids = Vec::new();
        for goal in goals {
            // Check if there are recent events for this goal
            let event_query = format!(
                "SELECT * FROM event WHERE entity_type = 'goal' AND entity_id = '{}' AND created_at > time::now() - {}d LIMIT 1",
                goal.goal_id, days_threshold
            );
            let mut event_result = self.store.get_db().query(&event_query).await.map_err(|e| {
                crate::errors::MetaError::SystemError(format!("Event query: {}", e))
            })?;

            let recent_events: Vec<Event> = event_result.take(0).unwrap_or_default();

            if recent_events.is_empty() {
                let event = Event::new(
                    "goal",
                    &goal.goal_id,
                    EventAction::Update,
                    "system",
                    json!({
                        "type": "goal_stale",
                        "reason": "no_activity",
                        "days_since_activity": days_threshold,
                        "title": goal.title
                    }),
                );
                let _ = self.store.log_event(&event).await;
                stale_ids.push(goal.goal_id.clone());
            }
        }
        Ok(stale_ids)
    }

    /// Proactive scan: Detect goals with excessive complexity (too many tasks)
    pub async fn scan_complex_goals(&self, task_threshold: usize) -> Result<Vec<String>> {
        let query = "SELECT goal_id, count() as task_count FROM work_item WHERE level = 'task' GROUP BY goal_id";
        let mut result =
            self.store.get_db().query(query).await.map_err(|e| {
                crate::errors::MetaError::SystemError(format!("Query error: {}", e))
            })?;

        #[derive(serde::Deserialize)]
        struct TaskCount {
            goal_id: String,
            task_count: i64,
        }

        let counts: Vec<TaskCount> = result
            .take(0)
            .map_err(|e| crate::errors::MetaError::SystemError(format!("Parse error: {}", e)))?;

        let mut complex_ids = Vec::new();
        for count in counts {
            if count.task_count as usize > task_threshold {
                let event = Event::new(
                    "goal",
                    &count.goal_id,
                    EventAction::Update,
                    "system",
                    json!({
                        "type": "goal_high_complexity",
                        "reason": "excessive_tasks",
                        "task_count": count.task_count,
                        "threshold": task_threshold,
                        "suggestion": "Consider breaking this goal into smaller subgoals"
                    }),
                );
                let _ = self.store.log_event(&event).await;
                complex_ids.push(count.goal_id);
            }
        }
        Ok(complex_ids)
    }

    /// Proactive scan: Detect phases ready for transition
    pub async fn scan_phase_transitions(&self) -> Result<Vec<String>> {
        let query = "SELECT * FROM phase WHERE status IN ['planned', 'active']";
        let mut result =
            self.store.get_db().query(query).await.map_err(|e| {
                crate::errors::MetaError::SystemError(format!("Query error: {}", e))
            })?;

        let phases: Vec<crate::Phase> = result
            .take(0)
            .map_err(|e| crate::errors::MetaError::SystemError(format!("Parse error: {}", e)))?;

        let mut transition_ids = Vec::new();
        for phase in phases {
            // Check if all dependencies are done
            if !phase.dependencies.is_empty() {
                let mut all_deps_done = true;
                for dep_id in &phase.dependencies {
                    let dep: Option<crate::Phase> = self
                        .store
                        .get_db()
                        .select(("phase", dep_id.as_str()))
                        .await
                        .map_err(|e| {
                            crate::errors::MetaError::SystemError(format!("Phase lookup: {}", e))
                        })?;

                    if let Some(d) = dep {
                        if d.status.to_lowercase() != "closed" {
                            all_deps_done = false;
                            break;
                        }
                    }
                }

                if all_deps_done && phase.status.to_lowercase() == "planned" {
                    let event = Event::new(
                        "phase",
                        &phase.phase_id,
                        EventAction::Update,
                        "system",
                        json!({
                            "type": "phase_ready_to_activate",
                            "reason": "dependencies_complete",
                            "title": phase.title
                        }),
                    );
                    let _ = self.store.log_event(&event).await;
                    transition_ids.push(phase.phase_id.clone());
                }
            }
        }
        Ok(transition_ids)
    }

    /// Run all proactive scans
    pub async fn run_all_scans(&self) -> Result<ScanReport> {
        let blocked = self.scan_blocked_goals().await?;
        let stale = self.scan_stale_goals(7).await?; // 7 days threshold
        let complex = self.scan_complex_goals(15).await?; // 15 tasks threshold
        let transitions = self.scan_phase_transitions().await?;

        Ok(ScanReport {
            blocked_goals: blocked,
            stale_goals: stale,
            complex_goals: complex,
            phases_ready: transitions,
        })
    }
}

#[derive(serde::Serialize)]
pub struct ScanReport {
    pub blocked_goals: Vec<String>,
    pub stale_goals: Vec<String>,
    pub complex_goals: Vec<String>,
    pub phases_ready: Vec<String>,
}
