// Parser module - DB-only architecture for entities
// Only FrontmatterParser and LinkExtractor remain for daily note editing

pub mod frontmatter;
pub mod links;

pub use frontmatter::FrontmatterParser;
pub use links::LinkExtractor;
