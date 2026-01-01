use metatheos_core::{Goal, Phase, Audit, Prompt, DailyNote, GoalStatus};
use metatheos_core::store::SurrealStore;
use tempfile::TempDir;
use chrono::NaiveDate;

/// Helper to create a temporary database for testing
async fn setup_test_store() -> (SurrealStore, TempDir) {
    let temp_dir = TempDir::new().unwrap();
    let db_path = temp_dir.path().join("test.db");
    let store = SurrealStore::init(db_path).await.unwrap();
    (store, temp_dir)
}

/// Helper to create a test goal
fn create_test_goal(goal_id: &str) -> Goal {
    Goal {
        goal_id: goal_id.to_string(),
        title: format!("Test Goal {}", goal_id),
        status: GoalStatus::Planned,
        phase: Some(4),
        dependencies: vec![],
        tags: vec!["test".to_string()],
        owner: Some("test-owner".to_string()),
        priority: None,
        estimate: None,
        actual: None,
        notes: None,
    }
}

#[tokio::test]
async fn test_store_create_and_read_goal() {
    let (store, _temp_dir) = setup_test_store().await;

    // Create a goal
    let goal = create_test_goal("G-TEST-001");
    let db = store.get_db();

    let created: Option<Goal> = db
        .create(("goals", goal.goal_id.as_str()))
        .content(goal.clone())
        .await
        .unwrap();

    assert!(created.is_some());

    // Read the goal back
    let read: Option<Goal> = db
        .select(("goals", goal.goal_id.as_str()))
        .await
        .unwrap();

    assert!(read.is_some());
    let read_goal = read.unwrap();
    assert_eq!(read_goal.goal_id, "G-TEST-001");
    assert_eq!(read_goal.title, "Test Goal G-TEST-001");
    assert_eq!(read_goal.status, GoalStatus::Planned);
}

#[tokio::test]
async fn test_store_update_goal() {
    let (store, _temp_dir) = setup_test_store().await;
    let db = store.get_db();

    // Create initial goal
    let mut goal = create_test_goal("G-TEST-002");
    let _: Option<Goal> = db
        .create(("goals", goal.goal_id.as_str()))
        .content(goal.clone())
        .await
        .unwrap();

    // Update the goal
    goal.status = GoalStatus::Active;
    goal.title = "Updated Test Goal".to_string();

    let updated: Option<Goal> = db
        .update(("goals", goal.goal_id.as_str()))
        .content(goal)
        .await
        .unwrap();

    assert!(updated.is_some());

    // Verify update
    let read: Option<Goal> = db
        .select(("goals", goal.goal_id.as_str()))
        .await
        .unwrap();

    let read_goal = read.unwrap();
    assert_eq!(read_goal.status, GoalStatus::Active);
    assert_eq!(read_goal.title, "Updated Test Goal");
}

#[tokio::test]
async fn test_store_delete_goal() {
    let (store, _temp_dir) = setup_test_store().await;
    let db = store.get_db();

    // Create a goal
    let goal = create_test_goal("G-TEST-003");
    let _: Option<Goal> = db
        .create(("goals", goal.goal_id.as_str()))
        .content(goal.clone())
        .await
        .unwrap();

    // Delete the goal
    let deleted: Option<Goal> = db
        .delete(("goals", goal.goal_id.as_str()))
        .await
        .unwrap();

    assert!(deleted.is_some());

    // Verify deletion
    let read: Option<Goal> = db
        .select(("goals", goal.goal_id.as_str()))
        .await
        .unwrap();

    assert!(read.is_none());
}

#[tokio::test]
async fn test_store_query_goals_by_status() {
    let (store, _temp_dir) = setup_test_store().await;
    let db = store.get_db();

    // Create multiple goals with different statuses
    for i in 1..=5 {
        let mut goal = create_test_goal(&format!("G-TEST-{:03}", i));
        goal.status = if i % 2 == 0 {
            GoalStatus::Active
        } else {
            GoalStatus::Planned
        };

        let _: Option<Goal> = db
            .create(("goals", goal.goal_id.as_str()))
            .content(goal)
            .await
            .unwrap();
    }

    // Query active goals
    let active_goals: Vec<Goal> = db
        .query("SELECT * FROM goals WHERE status = $status")
        .bind(("status", "active"))
        .await
        .unwrap()
        .take(0)
        .unwrap();

    assert_eq!(active_goals.len(), 2); // G-TEST-002 and G-TEST-004

    // Query planned goals
    let planned_goals: Vec<Goal> = db
        .query("SELECT * FROM goals WHERE status = $status")
        .bind(("status", "planned"))
        .await
        .unwrap()
        .take(0)
        .unwrap();

    assert_eq!(planned_goals.len(), 3); // G-TEST-001, G-TEST-003, G-TEST-005
}

#[tokio::test]
async fn test_store_create_and_read_phase() {
    let (store, _temp_dir) = setup_test_store().await;
    let db = store.get_db();

    // Create a phase
    let phase = Phase {
        phase_id: "PHASE_4".to_string(),
        title: "Test Phase 4".to_string(),
        status: "active".to_string(),
        description: Some("Test phase description".to_string()),
        start_date: None,
        end_date: None,
        goals: vec!["G-001".to_string(), "G-002".to_string()],
    };

    let created: Option<Phase> = db
        .create(("phases", phase.phase_id.as_str()))
        .content(phase.clone())
        .await
        .unwrap();

    assert!(created.is_some());

    // Read the phase back
    let read: Option<Phase> = db
        .select(("phases", phase.phase_id.as_str()))
        .await
        .unwrap();

    assert!(read.is_some());
    let read_phase = read.unwrap();
    assert_eq!(read_phase.phase_id, "PHASE_4");
    assert_eq!(read_phase.title, "Test Phase 4");
    assert_eq!(read_phase.goals.len(), 2);
}

#[tokio::test]
async fn test_store_create_and_read_audit() {
    let (store, _temp_dir) = setup_test_store().await;
    let db = store.get_db();

    // Create an audit
    let audit = Audit {
        audit_id: "AUDIT_TEST_001".to_string(),
        title: "Test Audit".to_string(),
        scope: "test-scope".to_string(),
        risk: "medium".to_string(),
        status: "open".to_string(),
        findings: Some("Test findings".to_string()),
        evidence: vec!["evidence1.md".to_string()],
        date: NaiveDate::from_ymd_opt(2025, 12, 31).unwrap(),
    };

    let created: Option<Audit> = db
        .create(("audits", audit.audit_id.as_str()))
        .content(audit.clone())
        .await
        .unwrap();

    assert!(created.is_some());

    // Read the audit back
    let read: Option<Audit> = db
        .select(("audits", audit.audit_id.as_str()))
        .await
        .unwrap();

    assert!(read.is_some());
    let read_audit = read.unwrap();
    assert_eq!(read_audit.audit_id, "AUDIT_TEST_001");
    assert_eq!(read_audit.title, "Test Audit");
    assert_eq!(read_audit.risk, "medium");
}

#[tokio::test]
async fn test_store_create_and_read_daily_note() {
    let (store, _temp_dir) = setup_test_store().await;
    let db = store.get_db();

    // Create a daily note
    let note = DailyNote {
        date: NaiveDate::from_ymd_opt(2025, 12, 31).unwrap(),
        phase: Some(4),
        goals_worked: vec!["G-001".to_string()],
        decisions_made: vec!["Decision 1".to_string()],
        divergences_noted: vec![],
    };

    let date_str = note.date.format("%Y-%m-%d").to_string();

    let created: Option<DailyNote> = db
        .create(("daily_notes", date_str.as_str()))
        .content(note.clone())
        .await
        .unwrap();

    assert!(created.is_some());

    // Read the note back
    let read: Option<DailyNote> = db
        .select(("daily_notes", date_str.as_str()))
        .await
        .unwrap();

    assert!(read.is_some());
    let read_note = read.unwrap();
    assert_eq!(read_note.date, NaiveDate::from_ymd_opt(2025, 12, 31).unwrap());
    assert_eq!(read_note.goals_worked.len(), 1);
}

#[tokio::test]
async fn test_store_bulk_operations() {
    let (store, _temp_dir) = setup_test_store().await;
    let db = store.get_db();

    // Create 10 goals in bulk
    for i in 1..=10 {
        let goal = create_test_goal(&format!("G-BULK-{:03}", i));
        let _: Option<Goal> = db
            .create(("goals", goal.goal_id.as_str()))
            .content(goal)
            .await
            .unwrap();
    }

    // Query all goals
    let all_goals: Vec<Goal> = db
        .query("SELECT * FROM goals WHERE goal_id LIKE $pattern")
        .bind(("pattern", "G-BULK-%"))
        .await
        .unwrap()
        .take(0)
        .unwrap();

    assert_eq!(all_goals.len(), 10);
}

#[tokio::test]
async fn test_store_concurrent_operations() {
    let (store, _temp_dir) = setup_test_store().await;

    // Spawn multiple concurrent operations
    let handles: Vec<_> = (1..=5)
        .map(|i| {
            let db = store.get_db().clone();
            tokio::spawn(async move {
                let goal = create_test_goal(&format!("G-CONCURRENT-{:03}", i));
                let _: Option<Goal> = db
                    .create(("goals", goal.goal_id.as_str()))
                    .content(goal)
                    .await
                    .unwrap();
            })
        })
        .collect();

    // Wait for all operations to complete
    for handle in handles {
        handle.await.unwrap();
    }

    // Verify all goals were created
    let db = store.get_db();
    let all_goals: Vec<Goal> = db
        .query("SELECT * FROM goals WHERE goal_id LIKE $pattern")
        .bind(("pattern", "G-CONCURRENT-%"))
        .await
        .unwrap()
        .take(0)
        .unwrap();

    assert_eq!(all_goals.len(), 5);
}
