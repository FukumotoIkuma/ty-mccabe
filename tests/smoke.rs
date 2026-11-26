//! 小さなプロジェクトで、数・終了コード・パスの出し方が使う人に約束したとおりであること。

use std::path::Path;
use std::process::{Command, Output};

const MODULE: &str = "\
def helper(x: int) -> int:
    if x > 0:
        return 1
    if x < 0:
        return -1
    return 0


def caller(x: int) -> int:
    if x == 10:
        return 10
    return helper(x)
";

/// 型が Any の値の属性は、同じ名前を持つ自分の property でありうる
const ANY_RECEIVER: &str = "\
import json


class Labeled:
    @property
    def label(self) -> str:
        return 'x'


def read() -> object:
    return json.loads('{}').label
";

fn project(files: &[(&str, &str)]) -> tempfile::TempDir {
    let dir = tempfile::tempdir().unwrap();
    for (path, text) in files {
        let path = dir.path().join(path);
        std::fs::create_dir_all(path.parent().unwrap()).unwrap();
        std::fs::write(path, text).unwrap();
    }
    dir
}

fn run(cwd: &Path, args: &[&str]) -> Output {
    Command::new(env!("CARGO_BIN_EXE_ty-mccabe")).current_dir(cwd).args(args).output().unwrap()
}

fn stdout(out: &Output) -> String {
    String::from_utf8(out.stdout.clone()).unwrap()
}

#[test]
fn counts_callees_and_exits_zero() {
    let dir = project(&[("pkg/__init__.py", ""), ("pkg/a.py", MODULE)]);
    let root = dir.path().to_str().unwrap();
    let out = run(dir.path(), &["--all", root, &format!("{root}/pkg")]);
    assert_eq!(out.status.code(), Some(0), "{}", String::from_utf8_lossy(&out.stderr));
    let text = stdout(&out);
    // 閾値は既定の 10。helper は分岐 2 つ。caller は自分の分岐 1 つに、閾値未満の helper の 2 つを足す
    assert!(text.lines().any(|l| l.starts_with("3\t3\t") && l.ends_with(" helper")), "{text}");
    assert!(text.lines().any(|l| l.starts_with("4\t2\t") && l.ends_with(" caller")), "{text}");
}

#[test]
fn callee_at_threshold_is_one_statement() {
    let dir = project(&[("pkg/__init__.py", ""), ("pkg/a.py", MODULE)]);
    let out = run(dir.path(), &["--all", "--threshold", "3", ".", "pkg"]);
    assert_eq!(out.status.code(), Some(0), "{}", String::from_utf8_lossy(&out.stderr));
    // helper は 3 で閾値以上なので、caller からは 1 つの文（caller は自分の分岐 1 つだけ）
    let text = stdout(&out);
    assert!(text.lines().any(|l| l.starts_with("2\t2\t") && l.ends_with(" caller")), "{text}");
}

#[test]
fn unknown_type_exits_one() {
    let dir = project(&[("pkg/__init__.py", ""), ("pkg/a.py", ANY_RECEIVER)]);
    let out = run(dir.path(), &[".", "pkg"]);
    assert_eq!(out.status.code(), Some(1), "{}", String::from_utf8_lossy(&out.stderr));
    assert!(
        stdout(&out).lines().any(|l| l.starts_with("分からない") && l.contains("pkg/a.py:11 json.loads(...).label")),
        "{}",
        stdout(&out)
    );
}

#[test]
fn relative_paths_are_shown_from_cwd() {
    let dir = project(&[("pkg/__init__.py", ""), ("pkg/a.py", MODULE)]);
    let out = run(dir.path(), &["--all", ".", "pkg"]);
    assert_eq!(out.status.code(), Some(0), "{}", String::from_utf8_lossy(&out.stderr));
    assert!(stdout(&out).lines().any(|l| l.ends_with("\tpkg/a.py:9 caller")), "{}", stdout(&out));
}

#[test]
fn usage_and_version() {
    let here = Path::new(env!("CARGO_MANIFEST_DIR"));
    assert_eq!(run(here, &[]).status.code(), Some(2));
    assert_eq!(run(here, &["--help"]).status.code(), Some(0));
    let version = run(here, &["--version"]);
    assert_eq!(version.status.code(), Some(0));
    assert!(stdout(&version).starts_with("ty-mccabe (ty "));
    // 調べるディレクトリが無い・知らない引数・数でない閾値は、道具が動けないので 2
    assert_eq!(run(here, &["."]).status.code(), Some(2));
    assert_eq!(run(here, &["--nope", ".", "."]).status.code(), Some(2));
    assert_eq!(run(here, &["--threshold", "x", ".", "."]).status.code(), Some(2));
}

#[test]
fn unreadable_or_broken_files_stop() {
    // 宣言した文字コードが UTF-8 でないファイル（ty は読めず、空のファイルとして扱う）
    let dir = project(&[("pkg/__init__.py", "")]);
    std::fs::write(dir.path().join("pkg/latin.py"), b"# coding: latin-1\ns = '\xe9'\n").unwrap();
    let out = run(dir.path(), &[".", "pkg"]);
    assert_eq!(out.status.code(), Some(2), "{}", String::from_utf8_lossy(&out.stderr));
    // 構文の誤り
    let dir = project(&[("pkg/__init__.py", ""), ("pkg/a.py", "def f(:\n    pass\n")]);
    let out = run(dir.path(), &[".", "pkg"]);
    assert_eq!(out.status.code(), Some(2), "{}", String::from_utf8_lossy(&out.stderr));
}

#[test]
fn same_file_is_counted_once() {
    let dir = project(&[("pkg/__init__.py", ""), ("pkg/a.py", MODULE)]);
    let out = run(dir.path(), &["--all", ".", "pkg", "pkg", "."]);
    assert_eq!(out.status.code(), Some(0), "{}", String::from_utf8_lossy(&out.stderr));
    assert_eq!(stdout(&out).lines().filter(|l| l.ends_with(" caller")).count(), 1, "{}", stdout(&out));
}

#[cfg(unix)]
#[test]
fn non_utf8_argument_stops() {
    use std::os::unix::ffi::OsStrExt;
    let here = Path::new(env!("CARGO_MANIFEST_DIR"));
    let out = Command::new(env!("CARGO_BIN_EXE_ty-mccabe"))
        .current_dir(here)
        .arg(".")
        .arg(std::ffi::OsStr::from_bytes(b"\xff"))
        .output()
        .unwrap();
    assert_eq!(out.status.code(), Some(2));
}

/// Python の版が違うプログラム（PEP 723 のスクリプトの設定）が混じっても、下位のクラスはそれぞれのプログラムで引く
#[test]
fn programs_are_kept_apart() {
    let a = "# /// script\n# [tool.ty.environment]\n# python-version = \"3.11\"\n# ///\n\ndef prime(x: object) -> str:\n    return str(x)\n";
    let b = "# /// script\n# [tool.ty.environment]\n# python-version = \"3.12\"\n# ///\n\nclass C:\n    def __str__(self) -> str:\n        if id(self) & 16:\n            return 'a'\n        return 'b'\n\n\ndef use(x: object, flag: bool) -> str:\n    if flag:\n        pass\n    return str(x)\n";
    let dir = project(&[("a.py", a), ("b.py", b)]);
    let out = run(dir.path(), &["--all", "--threshold", "3", ".", "."]);
    assert_eq!(out.status.code(), Some(0), "{}", String::from_utf8_lossy(&out.stderr));
    // 本来は、use の自分の分岐 1 つに、object の値の str が呼びうる C.__str__ の 1 つを足した 3。限界: ty は組み込みの
    // 関数が中で呼ぶ特殊メソッドを答えないので、今は use の自分の分岐だけの 2（docs/design.md の 8）
    let text = stdout(&out);
    assert!(text.lines().any(|l| l.starts_with("2\t2\t") && l.ends_with(" use")), "{text}");
}

const DISPATCH: &str = "\
class Base:
    def run(self, x: int) -> int:
        return 0


class Child(Base):
    def run(self, x: int) -> int:
        if x > 0:
            return 1
        if x < 0:
            return -1
        return 0


def use(b: Base, x: int) -> int:
    return b.run(x)
";

/// 受け手の型のメソッドを呼ぶ所は、ty の実装への移動が答える下位のクラスの上書きも数える
#[test]
fn subclass_override_is_counted() {
    let dir = project(&[("pkg/__init__.py", ""), ("pkg/a.py", DISPATCH)]);
    let out = run(dir.path(), &["--all", ".", "pkg"]);
    assert_eq!(out.status.code(), Some(0), "{}", String::from_utf8_lossy(&out.stderr));
    let text = stdout(&out);
    assert!(text.lines().any(|l| l.starts_with("3\t1\t") && l.ends_with(" use")), "{text}");
}

const CONSTRUCTOR: &str = "\
class Box:
    def __init__(self, x: int) -> None:
        if x > 0:
            self.x = x
        else:
            self.x = 0


def make() -> Box:
    return Box(1)
";

/// クラスを呼ぶ所は、ty が呼び出しの `(` で答えるコンストラクタを数える
#[test]
fn constructor_call_counts_init() {
    let dir = project(&[("pkg/__init__.py", ""), ("pkg/a.py", CONSTRUCTOR)]);
    let out = run(dir.path(), &["--all", ".", "pkg"]);
    assert_eq!(out.status.code(), Some(0), "{}", String::from_utf8_lossy(&out.stderr));
    let text = stdout(&out);
    assert!(text.lines().any(|l| l.starts_with("2\t1\t") && l.ends_with(" make")), "{text}");
}

const NESTED: &str = "\
def outer(x: int) -> int:
    def inner(y: int) -> int:
        if y > 0:
            return 1
        return 0

    if x > 0:
        return 2
    return 0
";

/// 中に書いた関数は外の関数と同じ組で、外の関数の C901 に入る分は外の関数だけの分岐から除く
#[test]
fn nested_function_is_grouped_with_outer() {
    let dir = project(&[("pkg/__init__.py", ""), ("pkg/a.py", NESTED)]);
    let out = run(dir.path(), &["--all", ".", "pkg"]);
    assert_eq!(out.status.code(), Some(0), "{}", String::from_utf8_lossy(&out.stderr));
    let text = stdout(&out);
    assert!(text.lines().any(|l| l.starts_with("3\t4\t") && l.ends_with(" outer")), "{text}");
    assert!(text.lines().any(|l| l.starts_with("3\t2\t") && l.ends_with(" outer.inner")), "{text}");
}
