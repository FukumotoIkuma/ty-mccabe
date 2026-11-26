//! 辺（docs/design.md の 4）: 単位の中の名前・属性・演算子・呼び出し・import の位置で、ty の公開の関数が答える定義へ引く。

use std::collections::{BTreeSet, HashMap, HashSet};

use ruff_db::files::File;
use ruff_db::parsed::{ParsedModuleRef, parsed_module};
use ruff_python_ast::name::Name;
use ruff_python_ast::visitor::source_order::{
    SourceOrderVisitor, TraversalSignal, walk_body, walk_decorator, walk_expr, walk_parameters, walk_type_params,
};
use ruff_python_ast::{self as ast, AnyNodeRef, Expr, ExprContext};
use ruff_source_file::LineIndex;
use ruff_text_size::{Ranged, TextSize};
use ty_ide::goto_definition;
use ty_module_resolver::file_to_module;
use ty_project::{ProjectDatabase, SemanticDb as _};
use ty_python_core::definition::DefinitionKind;
use ty_python_core::scope::NodeWithScopeKind;
use ty_python_core::semantic_index;
use ty_python_core::static_dunder_all::static_dunder_all;
use ty_python_semantic::types::ide_support::call_signature_details;
use ty_python_semantic::types::ide_support::mro_member_definitions;
use ty_python_semantic::types::match_pattern::{ClassPatternPositionalSource, class_pattern_positional_sources};
use ty_python_semantic::types::{PropertyAccessorRole, Type, binding_type};
use ty_python_semantic::{
    HasDefinition, HasType, ImplementationsFinder, ImportAliasResolution, ResolvedDefinition, SemanticModel,
    definitions_for_bin_op, definitions_for_imported_symbol, definitions_for_unary_op, map_stub_definition,
};

use crate::units::{Kind, Unit};

/// 定義の名前の位置（モジュールはファイルの頭）。
type At = (File, TextSize);

/// 辺と、分からない所（なぜ、どこ、どの単位の中）。
pub struct Edges {
    pub edges: Vec<HashSet<usize>>,
    pub unknown: BTreeSet<(&'static str, String, String)>,
}

pub fn edges<'db>(
    db: &'db ProjectDatabase,
    files: &[File],
    modules: &[ParsedModuleRef],
    shown: &[String],
    lines: &[LineIndex],
    units: &[Unit<'db>],
) -> Edges {
    let unit_at: HashMap<At, usize> =
        units.iter().enumerate().map(|(u, unit)| ((files[unit.file], unit.name), u)).collect();
    // 下位のクラスでの上書きが単位になりうるのは、同じ名前のメソッドの単位があるファイルだけ
    let mut method_files: HashMap<&str, Vec<File>> = HashMap::new();
    for unit in units.iter().filter(|u| u.kind == Kind::Function && u.scope.is_method_scope(db)) {
        let files_of = method_files.entry(unit.scope.name(db, &modules[unit.file])).or_default();
        if !files_of.contains(&files[unit.file]) {
            files_of.push(files[unit.file]);
        }
    }
    // Protocol のメンバーを使う所で動きうるメンバー: 調べるファイルのクラスと、そのインスタンスの型
    let classes = class_types(db, files, modules);
    let mut protocol_members_of: HashMap<(Type<'db>, Name, ExprContext), Vec<At>> = HashMap::new();
    // ty の `ImplementationsFinder::for_attribute` は、受け手の型・名前・読むか書くか消すかだけで答えを決める
    let mut members_of: HashMap<(Type<'db>, Name, ExprContext), Vec<At>> = HashMap::new();
    let mut edges = Vec::with_capacity(units.len());
    let mut unknown = BTreeSet::new();
    for unit in units {
        let program_file = db.program_file(files[unit.file]);
        let model = SemanticModel::new(db, program_file);
        let module = &modules[unit.file];
        let mut sites = Sites::default();
        match unit.scope.node(db) {
            NodeWithScopeKind::Module => walk_body(&mut sites, &module.syntax().body),
            NodeWithScopeKind::Function(f) => walk_body(&mut sites, &f.node(module).body),
            _ => unreachable!("単位は関数とモジュールの最上位"),
        }
        let at = |range: ruff_text_size::TextRange| {
            format!("{}:{}", shown[unit.file], lines[unit.file].line_index(range.start()))
        };

        // 関数（呼ぶ・値として書く所）と、モジュール（import する所）
        let mut functions: Vec<At> = Vec::new();
        let mut imported: Vec<At> = Vec::new();
        let goto = |offset: TextSize| -> Vec<At> {
            let targets = goto_definition(db, program_file, offset).into_iter().flatten();
            targets.map(|t| (t.file(), t.focus_range().start())).collect()
        };
        for name in sites.names {
            functions.extend(goto(name.start()));
        }
        // 位置で照らすクラスのパターンが読む属性（ty が `__match_args__`・dataclass の欄から答える名前）
        let mut pattern_attributes = sites.pattern_attributes;
        for pattern in &sites.class_patterns {
            let Some(Type::ClassLiteral(class)) = pattern.cls.inferred_type(&model) else {
                continue;
            };
            let positional = pattern.arguments.patterns.len();
            let env = model.program_environment();
            for source in class_pattern_positional_sources(db, &env, class, positional) {
                if let ClassPatternPositionalSource::Attribute(name) = source {
                    pattern_attributes.push(ast::ExprAttribute {
                        range: pattern.range(),
                        node_index: ast::AtomicNodeIndex::NONE,
                        value: pattern.cls.clone(),
                        attr: ast::Identifier::new(name, pattern.cls.range()),
                        ctx: ExprContext::Load,
                    });
                }
            }
        }
        for attribute in sites.attributes.iter().copied().chain(&pattern_attributes) {
            let Some(receiver) = attribute.value.inferred_type(&model) else {
                continue;
            };
            if is_dynamic(db, receiver) {
                unknown.insert((
                    "受け手の型が分からない",
                    format!("{} {}", at(attribute.range()), short(&Expr::Attribute(attribute.clone()))),
                    unit.qual.clone(),
                ));
            }
            let key = (receiver, attribute.attr.id.clone(), attribute.ctx);
            if !members_of.contains_key(&key) {
                let scan = method_files.get(attribute.attr.as_str()).map_or(&[][..], Vec::as_slice);
                let found = members(db, &model, attribute, scan);
                members_of.insert(key.clone(), found);
            }
            if matches!(receiver, Type::ProtocolInstance(_)) {
                // クラスのインスタンスを Protocol に代入できると ty が答えたクラスで、ty が継承の順で選ぶメンバー
                let found = protocol_members_of.entry(key.clone()).or_insert_with(|| {
                    let env = model.program_environment();
                    let role = match attribute.ctx {
                        ExprContext::Load => Some(PropertyAccessorRole::Getter),
                        ExprContext::Store => Some(PropertyAccessorRole::Setter),
                        ExprContext::Del => Some(PropertyAccessorRole::Deleter),
                        ExprContext::Invalid => None,
                    };
                    let mut out = Vec::new();
                    for (class, instance) in &classes {
                        if !instance.is_assignable_to(db, &env, receiver) {
                            continue;
                        }
                        if let Type::ClassLiteral(class) = class {
                            let found = mro_member_definitions(db, *class, attribute.attr.as_str(), role);
                            out.extend(member_definitions(db, &found.unwrap_or_default(), attribute.ctx));
                        }
                    }
                    out
                });
                functions.extend(found.iter().copied());
            }
            let found = &members_of[&key];
            if found.is_empty() {
                // 受け手がクラスのインスタンスでない（モジュールの属性など）ときは、定義への移動
                functions.extend(goto(attribute.attr.start()));
            } else {
                functions.extend(found.iter().copied());
            }
        }
        for op in sites.bin_ops {
            functions.extend(definitions_for_bin_op(&model, op).map(|(d, _)| resolved(db, &d)).unwrap_or_default());
        }
        for op in sites.unary_ops {
            functions.extend(definitions_for_unary_op(&model, op).map(|(d, _)| resolved(db, &d)).unwrap_or_default());
        }
        for call in sites.calls {
            // ty は、変えられるコンテナ（辞書・リスト）に入れた関数の型を、呼べるものの型（`Type::Callable`）に広げる。
            // その要素を呼ぶ所は、どの関数かを ty が決めていないので辿らない（関数は、表に名前を書いた単位で数える）
            if call.func.inferred_type(&model).is_some_and(|t| is_widened_callable(db, t)) {
                continue;
            }
            // overload の関数を呼ぶ所は、ty が呼び出しで答える宣言のほかに、関数の型が持つ実装
            if let Some(Type::FunctionLiteral(function)) = call.func.inferred_type(&model) {
                let definition = function.definition(db);
                functions.extend(resolved(db, &[ResolvedDefinition::Definition(definition)]));
            }
            // 呼び出しが呼ぶもの（クラスならコンストラクタ）
            for details in call_signature_details(&model, call) {
                let found: Vec<ResolvedDefinition> =
                    details.definition.into_iter().map(ResolvedDefinition::Definition).collect();
                functions.extend(resolved(db, &found));
            }
        }
        for offset in sites.imports {
            imported.extend(goto(offset));
        }
        for import in sites.star_imports {
            // `from m import *` は、ty が静的に読める m の `__all__` の名前を import する（サブモジュールなら、そのモジュール）
            let Some(file) = model.resolve_module(import.module.as_deref(), import.level).and_then(|m| m.file(db))
            else {
                continue;
            };
            for name in static_dunder_all(db, db.program_file(file)).unwrap_or_default() {
                let found = definitions_for_imported_symbol(
                    &model,
                    import,
                    name.as_str(),
                    ImportAliasResolution::ResolveAliases,
                );
                imported.extend(resolved(db, &found));
            }
        }
        for level in sites.relative_packages {
            if let Some(file) = model.resolve_module(None, level).and_then(|m| m.file(db)) {
                imported.extend(resolved(db, &[ResolvedDefinition::Module(db.program_file(file))]));
            }
        }
        if unit.kind == Kind::Module {
            imported.extend(parent_package(db, &model, files[unit.file]));
        }

        let mut targets: HashSet<usize> = functions
            .iter()
            .filter_map(|at| unit_at.get(at).copied())
            .filter(|t| units[*t].kind == Kind::Function)
            .collect();
        targets.extend(
            imported.iter().filter_map(|at| unit_at.get(at).copied()).filter(|t| units[*t].kind == Kind::Module),
        );
        edges.push(targets);
    }
    Edges { edges, unknown }
}

/// 属性が使うメンバーの定義（ty の言語サーバーの実装への移動が、属性の位置で使う `ImplementationsFinder::for_attribute`）。
/// 受け手の型の継承の順で選ばれるメンバーと、受け手の型の下位のクラスでの上書き。property は、読む・書く・消すに
/// 応じて getter・setter・deleter。実装への移動はプロジェクトのすべてのファイルを見るが、辺の先は調べるファイルの
/// メソッドの単位だけなので、同じ名前のメソッドの単位があるファイル（`files`）だけを見る。
fn members(db: &ProjectDatabase, model: &SemanticModel<'_>, attribute: &ast::ExprAttribute, files: &[File]) -> Vec<At> {
    let Some(finder) = ImplementationsFinder::for_attribute(model, attribute) else {
        return Vec::new();
    };
    let mut out = Vec::new();
    for file in files {
        let found = finder.implementations_for_file(db, db.program_file(*file)).unwrap_or_default();
        out.extend(member_definitions(db, &found, attribute.ctx));
    }
    out.extend(member_definitions(db, &finder.into_initial_definitions(), attribute.ctx));
    out
}

/// メンバーの定義の位置。クラスの本体で代入したメンバー（`m = f`・`p = property(f)`）は、ty が代入に付けた型の
/// 関数・property の accessor（読む・書く・消すに応じて getter・setter・deleter）。
fn member_definitions(db: &ProjectDatabase, found: &[ResolvedDefinition<'_>], ctx: ExprContext) -> Vec<At> {
    let mut assigned = Vec::new();
    for definition in found.iter().filter_map(ResolvedDefinition::definition) {
        if matches!(definition.kind(db), DefinitionKind::Function(_)) {
            continue;
        }
        // 値を入れない宣言（`x: int`）には、ty は代入の型を付けない
        let module = parsed_module(db, definition.python_file(db)).load(db);
        if !definition.kind(db).category(definition.file(db).is_stub(db), &module).is_binding() {
            continue;
        }
        let accessor = match binding_type(db, definition) {
            Type::PropertyInstance(property) => match ctx {
                ExprContext::Load => property.getter(db),
                ExprContext::Store => property.setter(db),
                ExprContext::Del => property.deleter(db),
                ExprContext::Invalid => None,
            },
            ty => Some(ty),
        };
        if let Some(Type::FunctionLiteral(function)) = accessor {
            assigned.push(ResolvedDefinition::Definition(function.definition(db)));
        }
    }
    let mut out = resolved(db, found);
    out.extend(resolved(db, &assigned));
    out
}

/// 定義の名前の位置。自分のプロジェクトの stub は、ty が実行時のソースへ写したもの。
fn resolved(db: &ProjectDatabase, found: &[ResolvedDefinition<'_>]) -> Vec<At> {
    let mut out = Vec::new();
    for definition in found {
        let mapped = map_stub_definition(db, definition, None).unwrap_or_else(|| vec![definition.clone()]);
        for definition in &mapped {
            let range = definition.focus_range(db);
            out.push((range.file(), range.start()));
        }
    }
    out
}

/// モジュールの親のパッケージ（ty のモジュールの解決が答える、名前の 1 つ上のモジュール）。
fn parent_package(db: &ProjectDatabase, model: &SemanticModel<'_>, file: File) -> Vec<At> {
    let Some(module) = file_to_module(db, db.program_file(file).resolver_file(db)) else {
        return Vec::new();
    };
    let Some(parent) = module.name(db).parent() else {
        return Vec::new();
    };
    let Some(package) = model.resolve_module(Some(parent.as_str()), 0) else {
        return Vec::new();
    };
    let Some(package_file) = package.file(db) else {
        return Vec::new();
    };
    resolved(db, &[ResolvedDefinition::Module(db.program_file(package_file))])
}

/// 調べるファイルのクラスの型と、そのインスタンスの型（ty がクラスの定義に付けた型から）。
fn class_types<'db>(
    db: &'db ProjectDatabase,
    files: &[File],
    modules: &[ParsedModuleRef],
) -> Vec<(Type<'db>, Type<'db>)> {
    let mut out = Vec::new();
    for (fi, file) in files.iter().enumerate() {
        let program_file = db.program_file(*file);
        let model = SemanticModel::new(db, program_file);
        let env = model.program_environment();
        for scope in semantic_index(db, program_file).scope_ids() {
            let Some(class) = scope.node(db).as_class() else {
                continue;
            };
            let class_ty = binding_type(db, class.node(&modules[fi]).definition(&model));
            if let Some(instance) = class_ty.to_instance_approximation(db, &env) {
                out.push((class_ty, instance));
            }
        }
    }
    out
}

/// ty が型を答えない（Any・Unknown。共用型の要素にあるものも）。
fn is_dynamic(db: &ProjectDatabase, ty: Type<'_>) -> bool {
    match ty {
        Type::Dynamic(_) => true,
        Type::Union(union) => union.elements(db).iter().any(|t| matches!(t, Type::Dynamic(_))),
        _ => false,
    }
}

/// ty が呼べるものの型に広げた型（共用型なら、要素がすべてそう）。
fn is_widened_callable(db: &ProjectDatabase, ty: Type<'_>) -> bool {
    match ty {
        Type::Callable(_) => true,
        Type::Union(union) => union.elements(db).iter().all(|t| matches!(t, Type::Callable(_))),
        _ => false,
    }
}

/// 出す式の短い形（呼び出しの引数と添字は省く）。
fn short(e: &Expr) -> String {
    match e {
        Expr::Name(n) => n.id.to_string(),
        Expr::Attribute(a) => format!("{}.{}", short(&a.value), a.attr),
        Expr::Call(c) => format!("{}(...)", short(&c.func)),
        Expr::Subscript(s) => format!("{}[...]", short(&s.value)),
        _ => "<式>".to_string(),
    }
}

/// 単位の中で、ty に定義を聞く位置。中に書いた関数の本体は、その関数の単位なので入らない（デコレータ・引数の既定値と
/// 注釈・戻り値の注釈・型引数は、def を実行する外の単位の中で評価される）。
#[derive(Default)]
struct Sites<'a> {
    names: Vec<&'a ast::ExprName>,
    attributes: Vec<&'a ast::ExprAttribute>,
    bin_ops: Vec<&'a ast::ExprBinOp>,
    unary_ops: Vec<&'a ast::ExprUnaryOp>,
    calls: Vec<&'a ast::ExprCall>,
    /// import する名前の、ドットで区切った部分それぞれの位置
    imports: Vec<TextSize>,
    /// `from . import x` の、モジュールを書かない相対の import の段
    relative_packages: Vec<u32>,
    /// クラスのパターン `case C(x=1)` の、パターンが読む `C.x`（属性の式として ty に聞く）
    pattern_attributes: Vec<ast::ExprAttribute>,
    /// クラスのパターン（位置で照らす属性は、ty が `__match_args__` などから答える）
    class_patterns: Vec<&'a ast::PatternMatchClass>,
    /// `from m import *`
    star_imports: Vec<&'a ast::StmtImportFrom>,
}

impl Sites<'_> {
    fn import_components(&mut self, name: &ast::Identifier) {
        let mut offset = name.start();
        for part in name.as_str().split('.') {
            self.imports.push(offset);
            offset += TextSize::of(part) + TextSize::of('.');
        }
    }
}

impl<'a> SourceOrderVisitor<'a> for Sites<'a> {
    fn enter_node(&mut self, node: AnyNodeRef<'a>) -> TraversalSignal {
        match node {
            AnyNodeRef::StmtFunctionDef(f) => {
                for decorator in &f.decorator_list {
                    walk_decorator(self, decorator);
                }
                if let Some(type_params) = f.type_params.as_deref() {
                    walk_type_params(self, type_params);
                }
                walk_parameters(self, &f.parameters);
                if let Some(returns) = f.returns.as_deref() {
                    walk_expr(self, returns);
                }
                return TraversalSignal::Skip;
            }
            AnyNodeRef::ExprName(name) => self.names.push(name),
            AnyNodeRef::ExprAttribute(attribute) => self.attributes.push(attribute),
            AnyNodeRef::ExprBinOp(op) => self.bin_ops.push(op),
            AnyNodeRef::ExprUnaryOp(op) => self.unary_ops.push(op),
            AnyNodeRef::ExprCall(call) => self.calls.push(call),
            AnyNodeRef::PatternMatchClass(pattern) => {
                self.class_patterns.push(pattern);
                for keyword in &pattern.arguments.keywords {
                    self.pattern_attributes.push(ast::ExprAttribute {
                        range: keyword.range(),
                        node_index: ast::AtomicNodeIndex::NONE,
                        value: pattern.cls.clone(),
                        attr: keyword.attr.clone(),
                        ctx: ExprContext::Load,
                    });
                }
            }
            AnyNodeRef::StmtImport(import) => {
                for alias in &import.names {
                    self.import_components(&alias.name);
                }
            }
            AnyNodeRef::StmtImportFrom(import) => {
                if let Some(module) = &import.module {
                    self.import_components(module);
                }
                // `from . import x` の x がサブモジュールなら、そのモジュール
                for alias in &import.names {
                    self.imports.push(alias.name.start());
                }
                if import.module.is_none() {
                    self.relative_packages.push(import.level);
                }
                if import.names.iter().any(|alias| alias.name.as_str() == "*") {
                    self.star_imports.push(import);
                }
            }
            _ => {}
        }
        TraversalSignal::Traverse
    }
}
