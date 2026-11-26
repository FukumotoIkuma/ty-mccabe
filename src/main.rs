//! 関数を分けても、分岐をほかの場所へ移しても下がらない McCabe の複雑度を出す（設計は docs/design.md）。
//!
//! 単位（関数・モジュールの最上位）の複雑度 = その単位と、そこから閾値未満の単位だけを通って辺を辿れる単位の、分岐の
//! 数の和 + 1。辺は、単位の中の名前・属性・演算子・呼び出し・import の位置で、ty の公開の関数が答える定義だけへ引く。
//! 分岐の数は ruff の C901 から。
//!
//! 使い方は USAGE。終了コードは、分からない所が無ければ 0、あれば 1、道具が動けなければ 2。

mod c901;
mod edges;
mod graph;
mod units;

use anyhow::{Context, Result};
use rayon::prelude::*;
use ruff_db::diagnostic::DiagnosticId;
use ruff_db::files::{File, system_path_to_file};
use ruff_db::parsed::{ParsedModuleRef, parsed_module};
use ruff_db::source::{line_index, source_text};
use ruff_db::system::{OsSystem, SystemPathBuf};
use ty_project::parallel::ParallelIteratorExt as _;
use ty_project::{ProjectDatabase, ProjectMetadata, SemanticDb as _};
use ty_python_semantic::types::check_types;

use ruff_linter::rules::mccabe::rules::function_is_too_complex::get_complexity_number;

use crate::units::{Kind, collect_py};

/// 道具が組み込んでいる ty の版（Cargo.toml の ruff のコミットが、この版の ty のもの）。プロジェクトの ty と
/// 版がそろうことは、wheel の依存（pyproject.toml の ty==）で uv・pip が確かめる。
const TY_VERSION: &str = "0.0.103";
/// 閾値の既定（ruff の C901 の max-complexity の既定と同じ）。
const DEFAULT_THRESHOLD: u32 = 10;

const USAGE: &str = "\
使い方: ty-mccabe [--list | --all] [--threshold <数>] [--explain <単位>] <ty のプロジェクトの根> <調べるディレクトリ>...

関数を分けても、分岐をほかの場所へ移しても下がらない McCabe の複雑度を出す。単位（関数・モジュールの最上位）と、
そこから閾値未満の単位だけを通って辿れる単位の、分岐の数の和に 1 を足した数。辺は、単位の中の名前・属性・演算子・
呼び出し・import の位置で ty が答える定義だけ。閾値以上の単位を呼ぶ所は 1 つの文。呼ぶ値の型を ty が答えない
（Any など）呼び出しがあれば、それを出して 1 で終える。

  (何も付けない)      分からない所と数の要約だけを出す（CI 向け）
  --list              複雑度が閾値以上の単位を、大きい順に出す
  --all               すべての単位を出す
  --threshold <数>    閾値（既定 10）
  --explain <単位>    行の末尾（例 `pkg/a.py:12 run`）がこれで終わる単位の、数に入れた単位と分岐の数を出す
  --version           版（組み込んだ ty の版）を出す

行の形: 複雑度<TAB>単位だけの複雑度（関数は ruff の C901 と同じ）<TAB>ファイル:行 クラス.関数（モジュールの最上位は <module>）
";

fn main() -> std::process::ExitCode {
    // UTF-8 でない引数は、ty が扱えないパスなので、道具が動けない（2）として止める
    let args: Vec<String> = match std::env::args_os().skip(1).map(|a| a.into_string()).collect::<Result<_, _>>() {
        Ok(args) => args,
        Err(a) => {
            eprintln!("ty-mccabe: UTF-8 でない引数: {}", a.to_string_lossy());
            return std::process::ExitCode::from(2);
        }
    };
    match args.first().map(String::as_str) {
        None | Some("-h" | "--help") => {
            print!("{USAGE}");
            return std::process::ExitCode::from(u8::from(args.is_empty()) * 2);
        }
        Some("-V" | "--version") => {
            println!("ty-mccabe (ty {TY_VERSION})");
            return std::process::ExitCode::SUCCESS;
        }
        _ => {}
    }
    match run(args) {
        Ok(true) => std::process::ExitCode::SUCCESS,
        Ok(false) => std::process::ExitCode::from(1),
        Err(e) => {
            eprintln!("ty-mccabe: {e:#}");
            std::process::ExitCode::from(2)
        }
    }
}

struct Options {
    /// None: 要約だけ、Some(false): 閾値以上、Some(true): すべて
    mode: Option<bool>,
    threshold: u32,
    explain: Option<String>,
    project: String,
    roots: Vec<String>,
}

fn options(args: Vec<String>) -> Result<Options> {
    let (mut mode, mut threshold, mut explain, mut positional) = (None, DEFAULT_THRESHOLD, None, Vec::new());
    let mut it = args.into_iter();
    while let Some(a) = it.next() {
        match a.as_str() {
            "--list" => mode = Some(false),
            "--all" => mode = Some(true),
            "--threshold" => {
                let v = it.next().context("--threshold の数")?;
                threshold = v.parse().with_context(|| format!("--threshold の数でない: {v}"))?;
                anyhow::ensure!(threshold >= 1, "--threshold は 1 以上");
            }
            "--explain" => explain = Some(it.next().context("--explain の単位")?),
            _ if a.starts_with("--") => anyhow::bail!("知らない引数: {a}\n\n{USAGE}"),
            _ => positional.push(a),
        }
    }
    let project = positional.first().cloned().context("ty のプロジェクトの根")?;
    let roots = positional[1..].to_vec();
    anyhow::ensure!(!roots.is_empty(), "調べるディレクトリを 1 つ以上渡す\n\n{USAGE}");
    Ok(Options { mode, threshold, explain, project, roots })
}

/// 分からない所が無ければ true。
fn run(args: Vec<String>) -> Result<bool> {
    let opts = options(args)?;
    // ty はパスを絶対パスで持つ。出すときは今のディレクトリからのパスにする
    let cwd = std::fs::canonicalize(std::env::current_dir()?)?;
    let utf8 = |p: std::path::PathBuf| {
        SystemPathBuf::from_path_buf(p).map_err(|p| anyhow::anyhow!("UTF-8 でないパス: {}", p.display()))
    };
    let project = utf8(std::path::absolute(&opts.project)?)?;
    let t = std::time::Instant::now();
    let system = OsSystem::new(&project);
    let mut metadata = ProjectMetadata::discover(&project, &system)?;
    metadata.apply_configuration_files(&system)?;
    let db = ProjectDatabase::fallible(metadata, system)?;
    let result = analyze(&db, &opts, &cwd, t);
    // 終わる前に ty の問い合わせの結果を捨てる手間を省く（ty の CLI と同じ）
    db.forget_storage_on_exit();
    result
}

fn print_unknown(unknown: &std::collections::BTreeSet<(&str, String, String)>) {
    for (kind, at, qual) in unknown {
        println!("分からない（{kind}）: {at}（{qual} の中）");
    }
}

/// 分からない所が無ければ true。
fn analyze(db: &ProjectDatabase, opts: &Options, cwd: &std::path::Path, t: std::time::Instant) -> Result<bool> {
    let utf8 = |p: std::path::PathBuf| {
        SystemPathBuf::from_path_buf(p).map_err(|p| anyhow::anyhow!("UTF-8 でないパス: {}", p.display()))
    };
    let mut paths = Vec::new();
    for r in &opts.roots {
        collect_py(&std::path::absolute(r)?, &mut paths).with_context(|| r.clone())?;
    }
    // 同じファイルを 2 度数えない（同じディレクトリを重ねて渡した・入れ子のディレクトリを渡した）
    let mut paths = paths.into_iter().map(std::fs::canonicalize).collect::<Result<Vec<_>, _>>()?;
    paths.sort();
    paths.dedup();
    let files: Vec<File> = paths
        .iter()
        .map(|p| system_path_to_file(db, &utf8(p.clone())?).map_err(|e| anyhow::anyhow!("{}: {e:?}", p.display())))
        .collect::<Result<_>>()?;
    let shown: Vec<String> = paths.iter().map(|p| p.strip_prefix(cwd).unwrap_or(p).display().to_string()).collect();
    let modules: Vec<ParsedModuleRef> =
        files.iter().map(|f| parsed_module(db, db.program_file(*f).python_file(db)).load(db)).collect();
    // 読めないファイル・構文の誤りのあるファイルは、数えずに通さない（ty は読めなければ空の文として扱う）
    let mut texts = Vec::new();
    for (fi, file) in files.iter().enumerate() {
        let source = source_text(db, *file);
        if let Some(e) = source.read_error() {
            anyhow::bail!("{}: 読めない: {e}", shown[fi]);
        }
        if let Some(e) = modules[fi].errors().first() {
            anyhow::bail!("{}: 構文の誤り: {}", shown[fi], e.error);
        }
        texts.push(source);
    }
    let lines: Vec<_> = files.iter().map(|f| line_index(db, *f)).collect();
    eprintln!("[段階] 準備: {:.2} 秒  ファイル {}", t.elapsed().as_secs_f64(), files.len());

    // 型推論を先に済ませる。ty check と同じく、ファイルを rayon で並べ、ジョブごとに ty のデータベースを複製して
    // check_types を呼ぶ（ty_project の map_with_db）。あとの問い合わせは、推論の結果を読むだけになる
    // ty が見つけた構文の誤り（同じ名前の引数など、構文解析の後で見つかるもの）のあるファイルも、数えずに通さない
    let t = std::time::Instant::now();
    let syntax_errors: Vec<Option<String>> = files
        .par_iter()
        .map_with_db(db, |db, file| {
            let diagnostics = check_types(db, db.program_file(*file));
            let error = diagnostics.iter().find(|d| d.id() == DiagnosticId::InvalidSyntax);
            error.map(|d| d.concise_message().to_string())
        })
        .collect();
    for (fi, error) in syntax_errors.iter().enumerate() {
        if let Some(message) = error {
            anyhow::bail!("{}: 構文の誤り: {message}", shown[fi]);
        }
    }
    eprintln!("[段階] 型推論: {:.2} 秒", t.elapsed().as_secs_f64());
    let t = std::time::Instant::now();
    let mut units = units::collect(db, &files, &modules, &shown, &lines);
    eprintln!("[段階] 単位: {:.2} 秒  単位 {}", t.elapsed().as_secs_f64(), units.len());

    // ── 単位ごとの分岐の数（docs/design.md の 2）──
    let t = std::time::Instant::now();
    let settings = c901::settings();
    let mut by_file: Vec<Vec<usize>> = vec![Vec::new(); files.len()];
    for (u, unit) in units.iter().enumerate() {
        by_file[unit.file].push(u);
    }
    for fi in 0..files.len() {
        let numbers = c901::numbers(&settings, &paths[fi], texts[fi].as_str(), (*modules[fi]).clone())?;
        for &u in &by_file[fi] {
            if units[u].kind == Kind::Function {
                units[u].own = *numbers
                    .get(&units[u].name.to_u32())
                    .with_context(|| format!("C901 が数を出さなかった関数: {}", units[u].qual))?;
            }
        }
    }
    // C901 は、中に書いた def を「1 + その def の本体の分岐」（= その def の C901 の数）として外の関数に足す（クラスの
    // 中に書いたものも）。単位だけの分岐は、単位の数から 1 と、中に書いた def それぞれの C901 の数を引いたもの
    // モジュールの最上位は、ruff の数え方（`get_complexity_number`）をモジュールの文に当て、関数の外に書いた def
    // （クラスの中も）の C901 の数を同じように引く
    let mut module_of = vec![usize::MAX; files.len()];
    for (u, unit) in units.iter_mut().enumerate() {
        if unit.kind == Kind::Module {
            module_of[unit.file] = u;
            unit.own = u32::try_from(get_complexity_number(&modules[unit.file].syntax().body))? + 1;
        }
    }
    let mut nested = vec![0i64; units.len()];
    for unit in &units {
        if unit.kind == Kind::Function {
            nested[unit.outer.unwrap_or(module_of[unit.file])] += i64::from(unit.own);
        }
    }
    for (unit, nested) in units.iter_mut().zip(nested) {
        let dec = i64::from(unit.own) - 1 - nested;
        anyhow::ensure!(dec >= 0, "C901 の数から単位だけの分岐を出せない: {}", unit.qual);
        unit.dec = dec as u32;
        // モジュールの最上位の、単位だけの複雑度（C901 は関数にしか数を出さないので、中の def を含めない）
        if unit.kind == Kind::Module {
            unit.own = unit.dec + 1;
        }
    }
    eprintln!("[段階] 分岐: {:.2} 秒", t.elapsed().as_secs_f64());

    // ── 辺（docs/design.md の 4）──
    let t = std::time::Instant::now();
    let edges::Edges { edges, unknown } = edges::edges(db, &files, &modules, &shown, &lines, &units);
    eprintln!("[段階] 辺: {:.2} 秒  辺 {}", t.elapsed().as_secs_f64(), edges.iter().map(|e| e.len()).sum::<usize>());

    // ── 足し合わせ（docs/design.md の 3）──
    // 中に書いた単位は外の関数と同じ組（中の単位から外への辺を足して組を作る）
    let n = units.len();
    let mut grouping = edges.clone();
    for (u, unit) in units.iter().enumerate() {
        if let Some(o) = unit.outer {
            grouping[u].insert(o);
            grouping[o].insert(u);
        }
    }
    let dec: Vec<u32> = units.iter().map(|u| u.dec).collect();
    let sums = graph::sums(&grouping, &dec, opts.threshold);

    if let Some(want) = &opts.explain {
        for u in (0..n).filter(|u| units[*u].qual.ends_with(want.as_str())) {
            let mut members: Vec<(u32, &str)> =
                sums.regions[sums.comp_of[u]].iter().map(|m| (units[*m].dec, units[*m].qual.as_str())).collect();
            members.sort_by(|a, b| b.cmp(a));
            println!("{} = {}", units[u].qual, sums.complexity[u]);
            for (d, q) in members {
                println!("  {d}\t{q}");
            }
        }
        print_unknown(&unknown);
        return Ok(unknown.is_empty());
    }

    let mut rows: Vec<(u32, u32, usize)> = Vec::new();
    let (mut over_own, mut over, mut counted) = (0, 0, 0);
    for (u, unit) in units.iter().enumerate() {
        counted += 1;
        over_own += usize::from(unit.own >= opts.threshold);
        over += usize::from(sums.complexity[u] >= opts.threshold);
        if opts.mode == Some(true) || (opts.mode == Some(false) && sums.complexity[u] >= opts.threshold) {
            rows.push((sums.complexity[u], unit.own, u));
        }
    }
    rows.sort_by(|a, b| b.0.cmp(&a.0).then(b.1.cmp(&a.1)).then(units[a.2].qual.cmp(&units[b.2].qual)));
    for (c, own, u) in rows {
        println!("{c}\t{own}\t{}", units[u].qual);
    }
    print_unknown(&unknown);
    eprintln!(
        "単位 {counted}（モジュール {}）  複雑度 {} 以上 {over}（単位だけで数えると {over_own}）  分からない所 {}",
        files.len(),
        opts.threshold,
        unknown.len()
    );
    // 分からない所があれば 1 で終える（測れない所を残さない）
    Ok(unknown.is_empty())
}
