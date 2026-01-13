use metatheos_core::store::SurrealStore;
use std::path::PathBuf;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let gov_root = PathBuf::from("/home/actpm/Documents/workfolder/aequitas/governance");
    let db_path = gov_root.join(".metatheos.db");

    println!("📊 Connecting to database at: {:?}", db_path);
    let store = SurrealStore::init(db_path).await?;

    // Check phases
    let phases = store.get_all_phases().await?;
    println!("\n✅ Total Phases: {}", phases.len());

    // Check goals
    let goals = store.get_all_goals().await?;
    println!("✅ Total Goals: {}", goals.len());

    println!("\n📋 Goals by Phase:");
    for phase in &phases {
        let phase_goals: Vec<_> = goals.iter()
            .filter(|g| g.phase_id == phase.phase_id)
            .collect();

        if !phase_goals.is_empty() {
            println!("\n  {} ({}):", phase.title, phase.phase_id);
            for goal in phase_goals {
                println!("    - {} [{}] - {}", goal.id, goal.status, goal.title);
            }
        }
    }

    // Check work items
    let db = store.get_db();
    let mut work_items_query = db.query("SELECT * FROM work_item").await?;
    let work_items: Vec<serde_json::Value> = work_items_query.take(0)?;

    println!("\n✅ Total Work Items: {}", work_items.len());

    println!("\n📋 Work Items by Goal:");
    for goal in &goals {
        let goal_work_items: Vec<_> = work_items.iter()
            .filter(|wi| wi.get("goal_id").and_then(|v| v.as_str()) == Some(&goal.id))
            .collect();

        if !goal_work_items.is_empty() {
            println!("\n  {} ({} tasks):", goal.title, goal_work_items.len());
            for wi in goal_work_items {
                let title = wi.get("title").and_then(|v| v.as_str()).unwrap_or("???");
                let status = wi.get("status").and_then(|v| v.as_str()).unwrap_or("???");
                println!("    - [{}] {}", status, title);
            }
        }
    }

    Ok(())
}
