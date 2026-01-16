use metatheos_core::store::SurrealStore;
use std::path::PathBuf;

#[tokio::main]
async fn main() {
    let db_path = PathBuf::from("/home/actpm/Documents/workfolder/aequitas/governance/.metatheos.db");
    
    let store = SurrealStore::init(db_path).await.expect("Failed to init DB");
    let db = store.get_db();
    
    // Count goals
    let mut goal_resp = db.query("SELECT count() FROM goal GROUP ALL").await.expect("Query failed");
    let goal_count: Option<serde_json::Value> = goal_resp.take(0).ok();
    println!("Goals: {:?}", goal_count);
    
    // Count work items
    let mut wi_resp = db.query("SELECT count() FROM work_item GROUP ALL").await.expect("Query failed");
    let wi_count: Option<serde_json::Value> = wi_resp.take(0).ok();
    println!("Work Items: {:?}", wi_count);
    
    // List all goals
    let mut goals_resp = db.query("SELECT id, phase_id, title, status FROM goal").await.expect("Query failed");
    let goals: Vec<serde_json::Value> = goals_resp.take(0).expect("Parse failed");
    println!("\n=== GOALS ===");
    for g in goals {
        println!("{}", serde_json::to_string_pretty(&g).unwrap());
    }
    
    // List all work items
    let mut wi_list_resp = db.query("SELECT id, goal_id, title, status FROM work_item ORDER BY goal_id, order_index").await.expect("Query failed");
    let work_items: Vec<serde_json::Value> = wi_list_resp.take(0).expect("Parse failed");
    println!("\n=== WORK ITEMS ({}) ===", work_items.len());
    for wi in work_items.iter().take(10) {
        println!("{}", serde_json::to_string_pretty(&wi).unwrap());
    }
    if work_items.len() > 10 {
        println!("... and {} more", work_items.len() - 10);
    }
}
