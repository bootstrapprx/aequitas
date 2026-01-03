use metatheos_core::governance::GovernanceContext;
use metatheos_core::llm::runtime::OllamaRuntimeController;
use metatheos_core::reasoner::intent::Intent;
use metatheos_core::reasoner::intent::IntentRouter;
use metatheos_core::reasoner::materializer::MarkdownMaterializer;
use metatheos_core::reasoner::validation::ValidationLayer;
use serde_json::json;
use std::fs;

fn setup_goal_fixture() -> tempfile::TempDir {
    let dir = tempfile::tempdir().unwrap();
    let goals_dir = dir.path().join("03_GOALS_EPICS");
    fs::create_dir_all(&goals_dir).unwrap();
    let goal_file = goals_dir.join("G-001.md");
    let content = r#"---
goal_id: G-001
title: Seed Goal
status: active
phase: P1
---
Seed content
"#;
    fs::write(goal_file, content).unwrap();
    dir
}

#[test]
fn validation_rejects_missing_dependency() {
    let dir = setup_goal_fixture();
    let ctx = GovernanceContext::load(dir.path()).unwrap();
    let doc = json!({
        "intent": "draft_goal",
        "id": "G-002",
        "title": "New Goal",
        "phase": "P1",
        "status": "active",
        "depends_on": ["G-999"],
        "canon_refs": [],
        "rationale": "Test",
        "body": "Body"
    });

    let report = ValidationLayer::validate(&doc, &Intent::DraftGoal, &ctx);
    assert!(!report.valid);
    assert!(report.errors.iter().any(|e| e.contains("Dependency")));
}

#[test]
fn intent_router_matches_rule_without_model() {
    // Test rule-based classification (no Ollama required)
    let guess = IntentRouter::classify_rule_based("create a new goal for onboarding").unwrap();
    assert_eq!(guess.intent, Intent::DraftGoal);

    // Test Ollama classification only if Ollama is available
    if let Ok(runtime) = OllamaRuntimeController::new(None, None) {
        if is_ollama_available() {
            let rt = tokio::runtime::Runtime::new().unwrap();
            let guess2 = rt
                .block_on(IntentRouter::classify("what is blocking", &runtime))
                .unwrap();
            assert_eq!(guess2.intent, Intent::AnalyzeBlockers);
        } else {
            eprintln!("Skipping Ollama test: server not available at http://127.0.0.1:11435");
        }
    }
}

// Helper to check if Ollama server is available
fn is_ollama_available() -> bool {
    std::net::TcpStream::connect("127.0.0.1:11435")
        .map(|_| true)
        .unwrap_or(false)
}

#[test]
fn materializer_builds_goal_draft() {
    let dir = setup_goal_fixture();
    let ctx = GovernanceContext::load(dir.path()).unwrap();
    let doc = json!({
        "intent": "draft_goal",
        "id": "G-010",
        "title": "Test Goal Draft",
        "phase": "P1",
        "status": "planned",
        "depends_on": ["G-001"],
        "canon_refs": [],
        "rationale": "Test",
        "body": "# Draft\nDetails"
    });

    let draft = MarkdownMaterializer::to_draft(&doc, &ctx.root, &ctx).unwrap();
    assert!(draft
        .target_path
        .to_string_lossy()
        .contains("03_GOALS_EPICS/G-010.md"));
    assert!(draft.frontmatter.contains("goal_id: G-010"));
    assert!(draft.body.contains("Draft"));
}
