//! ruff の C901 の数（ruff_linter を同じコミットで組み込み、C901 だけを閾値 0 で掛ける）。

use std::collections::HashMap;

use anyhow::{Context, Result};
use ruff_linter::linter::{ParseSource, lint_only};
use ruff_linter::registry::Rule;
use ruff_linter::settings::{LinterSettings, flags};
use ruff_linter::source_kind::SourceKind;
use ruff_python_ast::{ModModule, PySourceType};
use ruff_python_parser::Parsed;

pub fn settings() -> LinterSettings {
    LinterSettings {
        mccabe: ruff_linter::rules::mccabe::settings::Settings { max_complexity: 0 },
        ..LinterSettings::for_rules(vec![Rule::ComplexStructure])
    }
}

/// 関数の名前の位置 → C901 の数。閾値 0 なので、すべての関数の数が診断として出る。
/// `# noqa` と範囲で抑えるコメントは効かせない（数を隠せないように）。構文木は ty が解析したものを渡す。
pub fn numbers(
    settings: &LinterSettings,
    path: &std::path::Path,
    code: &str,
    parsed: Parsed<ModModule>,
) -> Result<HashMap<u32, u32>> {
    let source_type = PySourceType::from(path);
    let source_kind = SourceKind::Python { code: code.to_string(), is_stub: source_type.is_stub() };
    let result = lint_only(
        path,
        None,
        settings,
        flags::Noqa::Disabled,
        &source_kind,
        source_type,
        ParseSource::Precomputed(parsed),
    );
    let mut out = HashMap::new();
    for d in result.diagnostics {
        if !d.secondary_code().is_some_and(|c| c.as_str() == "C901") {
            continue;
        }
        let message = d.concise_message().to_string();
        // 「`名前` is too complex (数 > 0)」
        let number = message
            .rsplit_once('(')
            .and_then(|(_, rest)| rest.split_once(' '))
            .and_then(|(n, _)| n.parse().ok())
            .with_context(|| format!("{}: C901 の診断の文を読めない: {message}", path.display()))?;
        let range = d.range().with_context(|| format!("{}: C901 の診断に位置が無い", path.display()))?;
        out.insert(range.start().to_u32(), number);
    }
    Ok(out)
}
