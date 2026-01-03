use std::path::PathBuf;
use std::process::Command;

/// Helper to get the path to the metatheos CLI binary
fn cli_binary() -> PathBuf {
    let mut path = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    path.pop(); // Go up to workspace root
    path.push("target");
    path.push("debug");
    path.push("metatheos");
    path
}

/// Helper to get the governance root for tests
fn governance_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .parent()
        .unwrap()
        .join("governance")
}

#[test]
fn test_cli_audit_command() {
    let output = Command::new(cli_binary())
        .arg("audit")
        .arg("--root")
        .arg(governance_root())
        .arg("--format")
        .arg("json")
        .output()
        .expect("Failed to execute audit command");

    // Check that the command succeeded
    assert!(
        output.status.success(),
        "audit command failed with stderr: {}",
        String::from_utf8_lossy(&output.stderr)
    );

    // Parse JSON output - should be an array of audit records
    let stdout = String::from_utf8_lossy(&output.stdout);
    let result: serde_json::Value =
        serde_json::from_str(&stdout).expect("Failed to parse JSON output from audit command");

    // Verify it's an array
    assert!(result.is_array(), "Audit output should be a JSON array");

    // If there are audit records, verify structure
    if let Some(audits) = result.as_array() {
        if !audits.is_empty() {
            let first_audit = &audits[0];
            assert!(
                first_audit.get("title").is_some(),
                "Audit record should have 'title' field"
            );
            assert!(
                first_audit.get("date").is_some(),
                "Audit record should have 'date' field"
            );
            assert!(
                first_audit.get("scope").is_some(),
                "Audit record should have 'scope' field"
            );
        }
    }
}

#[test]
fn test_cli_goals_command() {
    let output = Command::new(cli_binary())
        .arg("goals")
        .arg("--root")
        .arg(governance_root())
        .arg("--format")
        .arg("json")
        .output()
        .expect("Failed to execute goals command");

    assert!(
        output.status.success(),
        "goals command failed with stderr: {}",
        String::from_utf8_lossy(&output.stderr)
    );

    let stdout = String::from_utf8_lossy(&output.stdout);
    let result: serde_json::Value =
        serde_json::from_str(&stdout).expect("Failed to parse JSON output from goals command");

    // Verify it's an array
    assert!(result.is_array(), "Goals output should be a JSON array");

    // If there are goals, verify structure
    if let Some(goals) = result.as_array() {
        if !goals.is_empty() {
            let first_goal = &goals[0];
            assert!(
                first_goal.get("goal_id").is_some(),
                "Goal should have 'goal_id' field"
            );
            assert!(
                first_goal.get("status").is_some(),
                "Goal should have 'status' field"
            );
            assert!(
                first_goal.get("title").is_some(),
                "Goal should have 'title' field"
            );
        }
    }
}

#[test]
fn test_cli_goals_filter_by_status() {
    // Test filtering by 'active' status
    let output = Command::new(cli_binary())
        .arg("goals")
        .arg("--root")
        .arg(governance_root())
        .arg("--status")
        .arg("active")
        .arg("--format")
        .arg("json")
        .output()
        .expect("Failed to execute goals --status command");

    assert!(
        output.status.success(),
        "goals --status command failed with stderr: {}",
        String::from_utf8_lossy(&output.stderr)
    );

    let stdout = String::from_utf8_lossy(&output.stdout);
    let result: serde_json::Value =
        serde_json::from_str(&stdout).expect("Failed to parse JSON output");

    // Verify all returned goals have 'active' status
    if let Some(goals) = result.as_array() {
        for goal in goals {
            if let Some(status) = goal.get("status").and_then(|s| s.as_str()) {
                assert_eq!(
                    status.to_lowercase(),
                    "active",
                    "Filtered goals should all have 'active' status"
                );
            }
        }
    }
}

#[test]
fn test_cli_phase_current() {
    let output = Command::new(cli_binary())
        .arg("phase")
        .arg("current")
        .arg("--root")
        .arg(governance_root())
        .output()
        .expect("Failed to execute phase current command");

    assert!(
        output.status.success(),
        "phase current command failed with stderr: {}",
        String::from_utf8_lossy(&output.stderr)
    );

    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(
        !stdout.is_empty(),
        "phase current should return phase information"
    );
}

#[test]
fn test_cli_today_show_flag() {
    let output = Command::new(cli_binary())
        .arg("today")
        .arg("--root")
        .arg(governance_root())
        .arg("--show")
        .output()
        .expect("Failed to execute today --show command");

    assert!(
        output.status.success(),
        "today --show command failed with stderr: {}",
        String::from_utf8_lossy(&output.stderr)
    );

    let stdout = String::from_utf8_lossy(&output.stdout);
    // Should output the path to today's note
    assert!(
        stdout.contains("01_DAILY"),
        "today --show should output path containing '01_DAILY'"
    );
}

#[test]
fn test_cli_help_flag() {
    let output = Command::new(cli_binary())
        .arg("--help")
        .output()
        .expect("Failed to execute --help command");

    assert!(output.status.success(), "--help command should succeed");

    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(
        stdout.contains("metatheos"),
        "Help output should contain 'metatheos'"
    );
    assert!(
        stdout.contains("audit"),
        "Help output should list 'audit' command"
    );
    assert!(
        stdout.contains("goals"),
        "Help output should list 'goals' command"
    );
}

#[test]
fn test_cli_version_flag() {
    let output = Command::new(cli_binary())
        .arg("--version")
        .output()
        .expect("Failed to execute --version command");

    assert!(output.status.success(), "--version command should succeed");

    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(
        stdout.contains("metatheos"),
        "Version output should contain 'metatheos'"
    );
}

#[test]
fn test_cli_invalid_root_path() {
    let output = Command::new(cli_binary())
        .arg("audit")
        .arg("--root")
        .arg("/nonexistent/path/to/governance")
        .output()
        .expect("Failed to execute command with invalid root");

    // Should fail with non-zero exit code
    assert!(
        !output.status.success(),
        "Command with invalid root should fail"
    );

    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(
        !stderr.is_empty(),
        "Error message should be printed to stderr"
    );
}
