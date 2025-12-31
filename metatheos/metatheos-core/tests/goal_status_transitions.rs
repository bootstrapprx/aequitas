use metatheos_core::{Goal, GoalStatus};

/// Test valid goal status transitions
#[test]
fn test_valid_status_transitions() {
    let valid_transitions = vec![
        // From active
        (GoalStatus::Active, GoalStatus::Blocked),
        (GoalStatus::Active, GoalStatus::Done),
        (GoalStatus::Active, GoalStatus::Archived),
        // From blocked
        (GoalStatus::Blocked, GoalStatus::Active),
        (GoalStatus::Blocked, GoalStatus::Archived),
        // From done
        (GoalStatus::Done, GoalStatus::Archived),
        // From partial
        (GoalStatus::Partial, GoalStatus::Active),
        (GoalStatus::Partial, GoalStatus::Done),
        (GoalStatus::Partial, GoalStatus::Archived),
    ];

    for (from, to) in valid_transitions {
        let result = validate_transition(&from, &to);
        assert!(
            result.is_ok(),
            "Transition from {:?} to {:?} should be valid",
            from,
            to
        );
    }
}

/// Test invalid goal status transitions
#[test]
fn test_invalid_status_transitions() {
    let invalid_transitions = vec![
        // Can't go from done to active/blocked/partial
        (GoalStatus::Done, GoalStatus::Active),
        (GoalStatus::Done, GoalStatus::Blocked),
        (GoalStatus::Done, GoalStatus::Partial),
        // Can't go from archived to anything
        (GoalStatus::Archived, GoalStatus::Active),
        (GoalStatus::Archived, GoalStatus::Blocked),
        (GoalStatus::Archived, GoalStatus::Done),
        (GoalStatus::Archived, GoalStatus::Partial),
        // Can't go from blocked to done directly
        (GoalStatus::Blocked, GoalStatus::Done),
        (GoalStatus::Blocked, GoalStatus::Partial),
    ];

    for (from, to) in invalid_transitions {
        let result = validate_transition(&from, &to);
        assert!(
            result.is_err(),
            "Transition from {:?} to {:?} should be invalid",
            from,
            to
        );
    }
}

/// Helper function to validate status transitions
/// Based on the rules defined in the README:
/// - active → blocked, completed, archived
/// - blocked → active, archived
/// - completed → archived
/// - partial → active, done, archived
fn validate_transition(from: &GoalStatus, to: &GoalStatus) -> Result<(), String> {
    match (from, to) {
        // From active
        (GoalStatus::Active, GoalStatus::Blocked) => Ok(()),
        (GoalStatus::Active, GoalStatus::Done) => Ok(()),
        (GoalStatus::Active, GoalStatus::Archived) => Ok(()),

        // From blocked
        (GoalStatus::Blocked, GoalStatus::Active) => Ok(()),
        (GoalStatus::Blocked, GoalStatus::Archived) => Ok(()),

        // From done
        (GoalStatus::Done, GoalStatus::Archived) => Ok(()),

        // From partial
        (GoalStatus::Partial, GoalStatus::Active) => Ok(()),
        (GoalStatus::Partial, GoalStatus::Done) => Ok(()),
        (GoalStatus::Partial, GoalStatus::Archived) => Ok(()),

        // From planned
        (GoalStatus::Planned, GoalStatus::Active) => Ok(()),
        (GoalStatus::Planned, GoalStatus::Archived) => Ok(()),

        // No-op: same status
        (a, b) if a == b => Ok(()),

        // All other transitions are invalid
        _ => Err(format!("Invalid transition from {:?} to {:?}", from, to)),
    }
}

#[test]
fn test_goal_creation_default_status() {
    let goal = Goal {
        goal_id: "G-TEST-001".to_string(),
        title: "Test Goal".to_string(),
        status: GoalStatus::Planned,
        phase: Some("4".to_string()),
        owner: None,
        parent_id: None,
        level: None,
        dependencies: vec![],
        canon: vec![],
        tags: vec![],
        updated: None,
        file_path: "test.md".into(),
        content: String::new(),
    };

    assert_eq!(goal.status, GoalStatus::Planned);
}

#[test]
fn test_goal_status_display() {
    assert_eq!(GoalStatus::Active.to_string(), "active");
    assert_eq!(GoalStatus::Blocked.to_string(), "blocked");
    assert_eq!(GoalStatus::Done.to_string(), "done");
    assert_eq!(GoalStatus::Archived.to_string(), "archived");
    assert_eq!(GoalStatus::Partial.to_string(), "partial");
    assert_eq!(GoalStatus::Planned.to_string(), "planned");
}
