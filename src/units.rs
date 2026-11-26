//! 単位（関数とモジュールの最上位。docs/design.md の 1）を、ty の意味の索引のスコープから作る。

use std::collections::HashMap;

use ruff_db::files::File;
use ruff_db::parsed::ParsedModuleRef;
use ruff_source_file::LineIndex;
use ruff_text_size::{Ranged, TextSize};
use ty_project::{ProjectDatabase, SemanticDb as _};
use ty_python_core::scope::{NodeWithScopeKind, ScopeId};
use ty_python_core::semantic_index;

#[derive(Clone, Copy, PartialEq, Eq)]
pub enum Kind {
    Module,
    Function,
}

pub struct Unit<'db> {
    /// 調べるファイルの番号
    pub file: usize,
    /// ty の意味の索引のスコープ
    pub scope: ScopeId<'db>,
    /// 名前の位置（ty が定義を答える位置で、C901 の数を引く鍵）。モジュールの最上位はファイルの頭
    pub name: TextSize,
    pub kind: Kind,
    /// `ファイル:行 クラス.関数`（モジュールの最上位は `ファイル:1 <module>`）
    pub qual: String,
    /// 囲む関数（クラスを通り抜けて最も近いもの）
    pub outer: Option<usize>,
    /// 単位だけの複雑度（関数は C901 の数。モジュールの最上位は 1）
    pub own: u32,
    /// 単位だけの分岐の数
    pub dec: u32,
}

/// スコープごとの、中に書いた関数の名前の前置きと、囲む関数。
struct Enclosing {
    prefix: String,
    function: Option<usize>,
}

pub fn collect<'db>(
    db: &'db ProjectDatabase,
    files: &[File],
    modules: &[ParsedModuleRef],
    shown: &[String],
    lines: &[LineIndex],
) -> Vec<Unit<'db>> {
    let mut units = Vec::new();
    for (fi, file) in files.iter().enumerate() {
        let index = semantic_index(db, db.program_file(*file));
        let mut enclosing: HashMap<ScopeId, Enclosing> = HashMap::new();
        // 外のスコープは中のスコープより先に出る（索引はスコープに入った順に番号を振る）
        for scope_id in index.scope_ids() {
            let parent = scope_id.scope(db).parent().map(|p| &enclosing[&index.scope_id(p)]);
            let (prefix, function) = parent.map_or((String::new(), None), |p| (p.prefix.clone(), p.function));
            let entry = match scope_id.node(db) {
                NodeWithScopeKind::Module => {
                    units.push(Unit {
                        file: fi,
                        scope: scope_id,
                        name: TextSize::default(),
                        kind: Kind::Module,
                        qual: format!("{}:1 <module>", shown[fi]),
                        outer: None,
                        own: 1,
                        dec: 0,
                    });
                    Enclosing { prefix, function }
                }
                NodeWithScopeKind::Function(f) => {
                    let name = f.node(&modules[fi]).name.range();
                    let qual = format!("{prefix}{}", scope_id.name(db, &modules[fi]));
                    units.push(Unit {
                        file: fi,
                        scope: scope_id,
                        name: name.start(),
                        kind: Kind::Function,
                        qual: format!("{}:{} {qual}", shown[fi], lines[fi].line_index(name.start())),
                        outer: function,
                        own: 0,
                        dec: 0,
                    });
                    Enclosing { prefix: format!("{qual}."), function: Some(units.len() - 1) }
                }
                NodeWithScopeKind::Class(_) => {
                    Enclosing { prefix: format!("{prefix}{}.", scope_id.name(db, &modules[fi])), function }
                }
                _ => Enclosing { prefix, function },
            };
            enclosing.insert(scope_id, entry);
        }
    }
    units
}

/// ディレクトリの下の `.py` のファイル。
pub fn collect_py(dir: &std::path::Path, out: &mut Vec<std::path::PathBuf>) -> std::io::Result<()> {
    for entry in std::fs::read_dir(dir)? {
        let path = entry?.path();
        // is_dir は、読めない（検索できない）ディレクトリを false にして黙って飛ばすので、誤りとして返す
        if std::fs::metadata(&path)?.is_dir() {
            collect_py(&path, out)?;
        } else if path.extension().is_some_and(|e| e == "py") {
            out.push(path);
        }
    }
    Ok(())
}
