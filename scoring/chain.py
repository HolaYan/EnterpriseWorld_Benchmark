#!/usr/bin/env python3
"""Long Horizon Completion Rate — the one way a run is read.

A node passes only if its own checks AND every ancestor's checks pass
(`coupling.closure_guard`; the final task's own checks judge the closing
result via `coupling.pin_final_task` + `coupling.bind_final_task`). Every node
carries a role (`coupling.tag_roles`): `required` = the final task or one of
its dependency ancestors — the subgraph the close-out needs; `optional` = an
isolated side probe or a branch feeding nothing the final task depends on.

Two metrics, nothing else:

    lhcr(run, "required")   share of REQUIRED nodes passing (closure verdict)
    lhcr(run, "all")        share of ALL 20 nodes passing (closure verdict)

both per instance, averaged by the caller over the shared denominator (a
missing run counts 0). Runs scored before the closure
guard existed carry per-node results without `ancestors_pass__*`; for those
`node_pass` composes the same verdict from the recorded per-node results
(own ∧ ancestors), and `closure_scored(run)` says which kind a run is.
"""
from __future__ import annotations

import functools
import json
from pathlib import Path

GRAPHS = Path(__file__).resolve().parents[1] / "instance"


@functools.lru_cache(maxsize=None)
def graph_meta(uid: str, graphs_root: str | None = None):
    """(nodes, dep, anc, depth, dmax, deepest) for one instance's DAG.
    depth(v) = longest `depends_on` chain ending at v (roots are 1)."""
    root = Path(graphs_root) if graphs_root else GRAPHS
    g = json.loads((root / uid / "g_exec.json").read_text())
    nodes = [n["node_id"] for n in g["nodes"]]
    dep = {n["node_id"]: list(n.get("depends_on") or []) for n in g["nodes"]}
    anc: dict[str, frozenset] = {}
    depth: dict[str, int] = {}

    def _r(v, stack=()):
        if v in anc:
            return
        if v in stack:                       # defensive: a cycle must not hang us
            anc[v], depth[v] = frozenset(), 1
            return
        for p in dep[v]:
            _r(p, stack + (v,))
        anc[v] = frozenset().union(*[anc[p] | {p} for p in dep[v]]) if dep[v] else frozenset()
        depth[v] = 1 + max((depth[p] for p in dep[v]), default=0)

    for v in nodes:
        _r(v)
    dmax = max(depth.values())
    return nodes, dep, anc, depth, dmax, [v for v in nodes if depth[v] == dmax]


def _own(run: dict, v: str) -> bool:
    return bool(((run.get("per_node") or {}).get(v) or {}).get("passed"))


def closure_scored(run: dict) -> bool:
    """True when the run's per-node results were produced by closure-guarded
    verifiers (the `ancestors_pass__*` check is present on some node)."""
    for pn in (run.get("per_node") or {}).values():
        for c in (pn or {}).get("checks") or []:
            if str(c.get("name", "")).startswith("ancestors_pass__"):
                return True
    return False


def node_pass(run: dict, v: str, graphs_root: str | None = None) -> bool:
    uid = run["graph"]
    if closure_scored(run):
        return _own(run, v)
    _n, _d, anc, _dp, _m, _deep = graph_meta(uid, graphs_root)
    return _own(run, v) and all(_own(run, a) for a in anc[v])



def node_own(run: dict, v: str) -> bool:
    """The node's own checks only — the closure check (`ancestors_pass__*`) is
    left out. For runs scored before the closure guard this is `passed`."""
    pn = (run.get("per_node") or {}).get(v) or {}
    checks = pn.get("checks") or []
    if not any(str(c.get("name", "")).startswith("ancestors_pass__") for c in checks):
        return bool(pn.get("passed"))
    return all(bool(c.get("ok")) for c in checks if not str(c.get("name", "")).startswith("ancestors_pass__"))


# ---------------------------------------------------------------- roles & LHCR
CLASSES = ("required", "optional", "all")


@functools.lru_cache(maxsize=None)
def roles(uid: str, graphs_root: str | None = None) -> dict:
    """{node: 'required'|'optional'} — from g_exec's `role` when present, else
    recomputed by the same rule (final task ∪ its ancestor closure)."""
    root = Path(graphs_root) if graphs_root else GRAPHS
    g = json.loads((root / uid / "g_exec.json").read_text())
    if all(n.get("role") in ("required", "optional") for n in g["nodes"]):
        return {n["node_id"]: n["role"] for n in g["nodes"]}
    nodes, _d, anc, _dp, _m, deep = graph_meta(uid, graphs_root)
    req = set(deep) | {a for v in deep for a in anc[v]}
    return {v: ("required" if v in req else "optional") for v in nodes}


def class_nodes(uid: str, cls: str, graphs_root: str | None = None) -> list[str]:
    nodes = graph_meta(uid, graphs_root)[0]
    if cls == "all":
        return list(nodes)
    r = roles(uid, graphs_root)
    return [v for v in nodes if r[v] == cls]


def lhcr(run: dict, cls: str = "required", graphs_root: str | None = None) -> float:
    """Long Horizon Completion Rate over the class — a BINARY verdict per run:
    1.0 iff EVERY node of the class passes the closure verdict (its own checks
    ∧ every ancestor's), else 0.0. For `required` this is exactly "the final
    task's own checks ∧ all of its ancestors' checks pass"; for `all` it is the
    same with the optional side branches added. Averaged over N it is a share
    of runs, never a share of nodes (partial credit lives only in the
    node-completion diagnostics below)."""
    vs = class_nodes(run["graph"], cls, graphs_root)
    return 1.0 if vs and all(node_pass(run, v, graphs_root) for v in vs) else 0.0
