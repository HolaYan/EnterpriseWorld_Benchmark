#!/usr/bin/env python3
"""Read one trajectory file and print its two headline verdicts plus the per-node closure verdicts.

    python3 scoring/score_run.py trajectories/S2_plan__gpt-5.6-sol__hybrid_balance_transfer_offer__0001.json

LHCR-Req = 1 iff the final task and every one of its dependency ancestors pass their own checks (closure verdict);
LHCR-All = the same with the optional side branches added. Both are binary per run; the paper averages them over
instances. The per-node verdicts here are read from the trajectory's recorded `per_node` checks, which the harness
computed on the saved final world state; no model call is needed.
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import chain

run = json.load(open(sys.argv[1]))
uid = run["graph"]
r = chain.roles(uid)
print(f"{uid}  model={run['model']}  mode={run['mode']}  tool_calls={run['n_tool_calls']}  stopped={run['stopped']}")
print(f"LHCR-Req = {chain.lhcr(run, 'required'):.0f}   LHCR-All = {chain.lhcr(run, 'all'):.0f}")
print()
print(f"{'node':6} {'role':9} {'own':4} {'closure':8} first failed check")
for v in chain.class_nodes(uid, "all"):
    pn = (run.get("per_node") or {}).get(v) or {}
    failed = [c["name"] for c in pn.get("checks") or [] if not c.get("ok")]
    print(f"{v:6} {r[v]:9} {'ok' if chain.node_own(run, v) else '--':4} {'ok' if chain.node_pass(run, v) else '--':8} {failed[0] if failed else ''}")
