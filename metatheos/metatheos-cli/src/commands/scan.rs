use anyhow::Result;
use metatheos_core::GovernanceContext;

pub fn run_scan(root: &str) -> Result<()> {
    let ctx = GovernanceContext::load(root)?;
    let summary = ctx.summary();

    println!("Governance root: {}", root);

    if let Some(phase) = summary.current_phase {
        println!("Current phase: {} — {}", phase.phase_id, phase.title);
    } else {
        println!("Current phase: not found");
    }

    println!(
        "Goals: total {}, active {}, blocked {}",
        summary.total_goals,
        summary.active_goals.len(),
        summary.blocked_goals.len()
    );

    if summary.today_exists {
        println!("Today's daily note: {}", summary.today_path.display());
    } else {
        println!(
            "Today's daily note: missing (expected at {})",
            summary.today_path.display()
        );
    }

    println!("\nRecent decisions:");
    if summary.recent_decisions.is_empty() {
        println!("- None found");
    } else {
        for decision in summary.recent_decisions {
            let status = decision
                .status
                .as_ref()
                .map(|s| s.to_string())
                .unwrap_or_else(|| "unknown".to_string());
            println!(
                "- {} [{}] — {}",
                decision.decision_id, status, decision.title
            );
        }
    }

    println!("\nCanon snapshot:");
    if summary.canon_docs.is_empty() {
        println!("- No canon documents found");
    } else {
        for doc in summary.canon_docs {
            println!("- {} ({})", doc.title, doc.file_path.display());
        }
    }

    println!("\nGovernance warnings:");
    if summary.warnings.is_empty() {
        println!("✓ None");
    } else {
        for warning in summary.warnings {
            println!("- {} [{}]", warning.message, warning.kind.to_string());
        }
    }

    Ok(())
}
