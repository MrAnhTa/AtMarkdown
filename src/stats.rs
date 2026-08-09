use regex::Regex;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct DocumentStats {
    pub lines: usize,
    pub words: usize,
    pub chars: usize,
    pub reading_time: usize,
}

pub struct StatsCalculator;

impl StatsCalculator {
    pub fn calculate(text: &str) -> DocumentStats {
        let lines = if text.is_empty() {
            0
        } else {
            text.lines().count()
        };

        let re_word = Regex::new(r"\b\w+\b").unwrap();
        let words = re_word.find_iter(text).count();
        let chars = text.chars().count();

        // Average reading speed: 200 words per minute
        let reading_time = if words > 0 {
            (words as f64 / 200.0).round().max(1.0) as usize
        } else {
            0
        };

        DocumentStats {
            lines,
            words,
            chars,
            reading_time,
        }
    }
}
