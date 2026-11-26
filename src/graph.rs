//! 複雑度の足し合わせ（docs/design.md の 3）: 単位と、そこから閾値未満の単位だけを通って辿れる単位の分岐の和 + 1。

use std::collections::HashSet;

/// 単位ごとの複雑度と、数えた範囲（分岐を持つ単位だけ）の組ごとの集まり・単位の組の番号。
pub struct Sums {
    pub complexity: Vec<u32>,
    pub comp_of: Vec<usize>,
    pub regions: Vec<HashSet<usize>>,
}

/// `edges` は、呼び出しの辺に、中に書いた関数と外の関数とのあいだの辺を足したもの（同じ組になる）。
pub fn sums(edges: &[HashSet<usize>], dec: &[u32], threshold: u32) -> Sums {
    let n = edges.len();
    let mut complexity = vec![0u32; n];
    let mut comp_of = vec![usize::MAX; n];
    // 範囲には、分岐を持つ単位だけを入れる（分岐の無い単位は数に効かない）
    let mut regions: Vec<HashSet<usize>> = Vec::new();
    // 強連結成分は、呼ぶ先の成分が先に出る順で並ぶ
    for comp in strongly_connected(edges) {
        let ci = regions.len();
        for &m in &comp {
            comp_of[m] = ci;
        }
        let mut region: HashSet<usize> = comp.iter().copied().filter(|m| dec[*m] > 0).collect();
        for &m in &comp {
            for &g in &edges[m] {
                let cg = comp_of[g];
                if cg == ci {
                    continue;
                }
                assert!(cg < ci, "呼ぶ先の成分が先に出ていない");
                // 呼ぶ先は閾値未満のときだけ展開する（閾値以上は 1 つの文）
                if complexity[g] < threshold {
                    region.extend(regions[cg].iter().copied());
                }
            }
        }
        let c = region.iter().map(|x| dec[*x]).sum::<u32>() + 1;
        for &m in &comp {
            complexity[m] = c;
        }
        regions.push(region);
    }
    Sums { complexity, comp_of, regions }
}

/// 強連結成分（Tarjan の方法。再帰を使わない）。辺の先の成分が先に出る順で返す。
fn strongly_connected(edges: &[HashSet<usize>]) -> Vec<Vec<usize>> {
    let n = edges.len();
    let succ: Vec<Vec<usize>> = edges
        .iter()
        .map(|e| {
            let mut v: Vec<usize> = e.iter().copied().collect();
            v.sort_unstable();
            v
        })
        .collect();
    let (mut index, mut low, mut on_stack) = (vec![usize::MAX; n], vec![0; n], vec![false; n]);
    let (mut next, mut stack, mut out) = (0, Vec::new(), Vec::new());
    for root in 0..n {
        if index[root] != usize::MAX {
            continue;
        }
        // (節, 次に見る辺の位置)
        let mut work = vec![(root, 0usize)];
        index[root] = next;
        low[root] = next;
        next += 1;
        stack.push(root);
        on_stack[root] = true;
        while let Some(&mut (v, ref mut i)) = work.last_mut() {
            if let Some(&w) = succ[v].get(*i) {
                *i += 1;
                if index[w] == usize::MAX {
                    index[w] = next;
                    low[w] = next;
                    next += 1;
                    stack.push(w);
                    on_stack[w] = true;
                    work.push((w, 0));
                } else if on_stack[w] {
                    low[v] = low[v].min(index[w]);
                }
                continue;
            }
            work.pop();
            if let Some(&(parent, _)) = work.last() {
                low[parent] = low[parent].min(low[v]);
            }
            if low[v] == index[v] {
                let mut comp = Vec::new();
                loop {
                    let w = stack.pop().expect("成分の節が積んである");
                    on_stack[w] = false;
                    comp.push(w);
                    if w == v {
                        break;
                    }
                }
                out.push(comp);
            }
        }
    }
    out
}
