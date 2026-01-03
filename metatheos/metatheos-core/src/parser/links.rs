use regex::Regex;

pub struct LinkExtractor;

impl LinkExtractor {
    /// Extract wiki-style links from markdown content: [[G-001]], [[D-015]], etc.
    pub fn extract_goal_links(content: &str) -> Vec<String> {
        Self::extract_all_links(content)
            .into_iter()
            .filter(|link| {
                let lower = link.to_lowercase();
                lower.starts_with("g-") || lower.starts_with("goal-") || lower.contains("goal")
            })
            .collect()
    }

    pub fn extract_decision_links(content: &str) -> Vec<String> {
        Self::extract_all_links(content)
            .into_iter()
            .filter(|link| {
                let lower = link.to_lowercase();
                lower.starts_with("d-") || lower.contains("decision")
            })
            .collect()
    }

    pub fn extract_all_links(content: &str) -> Vec<String> {
        let re = Regex::new(r"\[\[([^\]]+)\]\]").unwrap();
        re.captures_iter(content)
            .filter_map(|cap| cap.get(1).map(|m| m.as_str().to_string()))
            .collect()
    }
}
