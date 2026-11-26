//! 迂回の例（tests/fixture/evade/）の、行に書いた期待（`# 期待 <数>` か `# 期待 分からない`）と、道具が閾値 8 で
//! 出した複雑度・分からないとした単位が同じこと。モジュールの最上位の期待は `# <module> 期待 <数>` の行に書く。期待と結果は、ファイルと定義の行で照らす（同じ名前の関数・
//! メソッドも区別する）。
//!
//! ty が答えないために本来の数にならない例は、期待の後ろに `限界 <今の数>（理由）` を書き、今の数と照らす
//! （docs/design.md の 8）。ty の答えが増えて数が変われば落ちるので、限界を書き直す。

use std::collections::{BTreeMap, BTreeSet};
use std::path::Path;
use std::process::Command;

/// `ファイル:行 クラス.関数` の `ファイル:行 関数`（同じ行のモジュールの最上位と lambda を区別する）。
fn location(qual: &str) -> String {
    let (loc, name) = qual.split_once(' ').unwrap_or((qual, ""));
    format!("{loc} {}", name.rsplit('.').next().unwrap_or(name))
}

/// `期待 <数>` の後ろに `限界 <数>` があれば、限界の数（今の道具が出す数）。無ければ期待の数。
fn expected_value(mark: &str) -> String {
    let mark = mark.split_once("限界 ").map_or(mark, |(_, limit)| limit);
    mark.chars().take_while(|c| !matches!(c, '（' | ' ')).collect()
}

#[test]
fn evasions_are_measured() {
    let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("tests/fixture");
    let mut expected: BTreeMap<String, String> = BTreeMap::new();
    let mut files: Vec<_> = std::fs::read_dir(root.join("evade")).unwrap().map(|e| e.unwrap().path()).collect();
    files.sort();
    for path in files.iter().filter(|p| p.extension().is_some_and(|e| e == "py")) {
        let name = path.file_name().unwrap().to_string_lossy();
        for (i, line) in std::fs::read_to_string(path).unwrap().lines().enumerate() {
            // モジュールの最上位の期待は `# <module> 期待 <数>` の行に書く（行は 1）
            if let Some(mark) = line.strip_prefix("# <module> 期待 ") {
                expected.insert(format!("evade/{name}:1 <module>"), expected_value(mark));
                continue;
            }
            let (Some(def), Some((_, mark))) = (line.trim_start().strip_prefix("def "), line.split_once("# 期待 "))
            else {
                continue;
            };
            let func: String = def.chars().take_while(|c| c.is_alphanumeric() || *c == '_').collect();
            expected.insert(format!("evade/{name}:{} {func}", i + 1), expected_value(mark));
        }
    }
    assert!(expected.len() >= 90, "期待を書いた例が読めていない: {expected:?}");

    let out = Command::new(env!("CARGO_BIN_EXE_ty-mccabe"))
        .current_dir(&root)
        .args(["--all", "--threshold", "8", ".", "evade"])
        .output()
        .unwrap();
    let stdout = String::from_utf8(out.stdout).unwrap();
    let mut got: BTreeMap<String, String> = BTreeMap::new();
    let mut unknown: BTreeSet<String> = BTreeSet::new();
    for line in stdout.lines() {
        if let Some(rest) = line.strip_prefix("分からない") {
            let qual = rest.rsplit_once('（').and_then(|(_, q)| q.strip_suffix(" の中）")).unwrap();
            unknown.insert(location(qual));
        } else {
            let cols: Vec<&str> = line.split('\t').collect();
            let previous = got.insert(location(cols[2]), cols[0].to_string());
            assert!(previous.is_none(), "同じ関数が 2 回出た: {line}");
        }
    }

    let mut wrong = Vec::new();
    for (at, want) in &expected {
        let ok = if want == "分からない" {
            unknown.contains(at)
        } else {
            got.get(at) == Some(want) && !unknown.contains(at)
        };
        if !ok {
            wrong.push(format!("{at}: 期待 {want} / 出た {:?}（分からない: {}）", got.get(at), unknown.contains(at)));
        }
    }
    for at in unknown.iter().filter(|a| !expected.contains_key(*a)) {
        wrong.push(format!("{at}: 期待を書いていない関数を分からないとした"));
    }
    assert!(wrong.is_empty(), "{}\n{}", wrong.join("\n"), String::from_utf8_lossy(&out.stderr));
    // 分からないものがあるので 1 で終える
    assert_eq!(out.status.code(), Some(1));
}
