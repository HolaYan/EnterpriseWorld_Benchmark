# EnterpriseWorld: A realistic world for enterprise long-horizon agents

In enterprise workflows, agents must carry the results, records, and state changes of earlier operations into later ones, often across systems. **EnterpriseWorld** is a benchmark of 200 cross-system enterprise workflows with 20 operations each, built with **EnterpriseFlow**, a programmatic framework that constructs workflows around four design principles: *realistic* enterprise operations, *long-horizon* coordination, *structural control* over task dependencies, and *verifiable* local and cross-task outcomes. Dependencies are grounded in results and state changes produced by earlier operations, verified by tracing input origins and testing whether upstream errors affect downstream success, and audited by humans (97.2% agreement). Paired workflow variants either modify the required dependency topology or add task/tool distractors while preserving it.

**[Project page](https://holayan.github.io/EnterpriseWorld_Benchmark/) · Paper (To update) · Contact: hongjunliu@nyu.edu**

---
## What is in this repository

| path | contents |
|---|---|
| `instance/<id>/` | one workflow: the two queries, desk notes, oracle sidecars, the executable 20-operation graph, the gold trace, and six perturbation variants |
| `trajectories/<id>/` | real runs with the harness's per-operation verdicts; `trajectories/case_study.md` walks through one run step by step |
| `scoring/` | `chain.py`, the LHCR reader, and `score_run.py`, which prints a trajectory's verdicts |
| `DATA_SOURCES.md` | the upstream datasets merged into the world and their licences |

Ten workflows were chosen so that **every evaluated model fails them in the default setting (S2)**, one per business-function category of the benchmark. The eleventh, `hybrid_balance_transfer_offer__0001`, is the case study of the paper and of the project page.

| instance | category | depth | required / operations | S2 trajectories (all fail) | variants |
|---|---|---|---|---|---|
| `hybrid_mobile_deposit_hold__0001` | Banking & Payments | 12 | 15 / 20 | Astra, Sol, Opus, Gemini | 6 |
| `hybrid_loyalty_ticket_redemption__0001` | Customer Service & Disputes | 12 | 15 / 20 | Astra, Sol, Opus, Gemini | 6 |
| `hybrid_dividend_distribution__0001` | Finance & Treasury | 13 | 17 / 20 | Astra, Sol, Opus, Gemini | 6 |
| `hybrid_employee_leave_approval__0001` | HR & People Operations | 12 | 16 / 20 | Astra, Sol, Opus, Gemini | 6 |
| `hybrid_dental_insurance_prior_auth__0001` | Healthcare & Clinical | 14 | 18 / 20 | Astra, Sol, Opus, Gemini | 6 |
| `hybrid_change_management__0001` | IT & Service Management | 13 | 18 / 20 | Astra, Sol, Opus, Gemini | 6 |
| `hybrid_franchise_royalty_reconciliation__0001` | Legal, Contracts & IP | 14 | 18 / 20 | Astra, Sol, Opus, Gemini | 6 |
| `hybrid_debt_covenant_amendment__0001` | Risk, Fraud & Compliance | 13 | 17 / 20 | Astra, Sol, Opus, Gemini | 6 |
| `hybrid_deal_desk_approval__0001` | Sales, Marketing & Partnerships | 14 | 18 / 20 | Astra, Sol, Opus, Gemini | -- |
| `hybrid_lot_recall_notification__0001` | Supply Chain & Operations | 14 | 18 / 20 | Astra, Sol, Fable, Opus, Gemini | 6 |
| `hybrid_balance_transfer_offer__0001` | Banking & Payments (case study) | 12 | 17 / 20 | Sol, all four settings | 6 |

Astra = GPT-6 Astra, Sol = GPT-5.6 Sol, Fable = Claude Fable 5.1 (evaluated on a 50-workflow subset, hence present on one of the ten), Opus = Claude Opus 4.8, Gemini = Gemini 3.7 Flash. Depth is the longest dependency path in the required graph. **Required operations** are the case-closing operation and everything on the dependency path to it; the remaining **side operations** are part of the business event but do not enter that path. Variants exist for the workflows that were in the perturbation sweep.

## Quick start

Score a shipped trajectory (no model call and no world download needed; the per-operation verdicts are recorded in the file):

```
python3 scoring/score_run.py trajectories/hybrid_balance_transfer_offer__0001/S2_plan__gpt-5.6-sol__hybrid_balance_transfer_offer__0001.json
```

This prints the two headline verdicts and a per-operation table (role, own check, closure check, first failed check).

Run your own agent on a workflow:

1. Download the workflow's initial world (see [World snapshots](#world-snapshots)) and decompress it to a SQLite file.
2. Expose the five tools listed in `instance.json` → `agent_visible.tools` over that connection: `query` (read-only `SELECT`), `describe_table`, `create_row`, `update_row`, `delete_row`.
3. Give the agent the query of the setting you want (see [The four settings](#the-four-settings)); under S2 and above, return each clause of `s2_constraints.json` in the tool response the first time the agent works one of the tables it is bound to.
4. After the run, execute the checks in `g_exec.json` against the final database. Each check is a SQL query with an expected value; an operation passes only if its own checks and every ancestor's checks pass (compose along `depends_on`).

The harness that does this for the models in the paper is released with the full dataset.

## Layout of an instance

```
instance/hybrid_balance_transfer_offer__0001/
  overall_query_detailed.txt   S1 query: the goal with every step spelled out
  overall_query_plan.txt       S2 query: the goal only; the agent plans the steps itself
  s2_constraints.json          desk notes: policy clauses the world surfaces just in time (S2 and above)
  oracle_map.json              S3 sidecar: Dependency-Map Oracle (which upstream operations constrain each consumer, and how)
  oracle_handoff.json          S4 sidecar: Handoff Oracle (the correct dependency object, delivered when the consumer needs it)
  instance.json                agent_visible (query, world summary, conventions, tool list) + hidden (gold DAG, verifier)
  g_exec.json                  the executable 20-operation DAG: R/W field sets, dependency edges, per-operation checks, roles
  gt_trace.json                the gold trace: the figure each operation writes and the SQL recipe that yields it
  world_s0.sqlite.gz           the merged initial world the agent acts on (downloaded separately)
  perturbations/               six variants: bridge__k1, bridge__k3, bridge__k5, gate__p3, distractor__d10, tool__x10
trajectories/<instance>/       S2 runs of every model on the ten all-fail workflows; S1–S4 of GPT-5.6 Sol on the case study
```

Every operation (node) of the graph is the tuple

```
(instruction, skills, tools, context, artifacts{A_in, A_out}, R, W, action_semantics, source, verifier, role)
```

`R` and `W` are field-level read and write sets; an edge `a → b` exists only where `W(a) ∩ R(b) ≠ ∅` on a shared entity, and each edge names the value, record, state, or prerequisite it carries. `role` is `required` or `optional` (a side operation). The `hidden` half of `instance.json` and the checks in `g_exec.json` are never shown to the agent.

## The four settings

| setting | what the agent receives | file |
|---|---|---|
| S1 detailed (the **Procedure Oracle** of the paper) | the goal with every step written out | `overall_query_detailed.txt` |
| S2 plan (**default**) | the goal only; policy clauses arrive as desk notes when the agent first touches the tables they govern | `overall_query_plan.txt` + `s2_constraints.json` |
| S3 = S2 + **Dependency-Map Oracle** | S2, plus for each consumer operation which upstream operations constrain it and the dependency type (no values) | `oracle_map.json` |
| S4 = S2 + **Handoff Oracle** | S2, plus the correct dependency object handed over when the consumer needs it | `oracle_handoff.json` |

Oracles travel through the same desk-note channel as the policy clauses, so a trajectory records what was delivered and when.

## Scoring

The world is scored **after** the run, on the saved final state. An operation passes only if its own checks **and** every dependency ancestor's checks pass (the closure verdict). Two numbers per run, both binary:

- **LHCR-Req** (Long-Horizon Completion Rate, Required) = 1 iff the case-closing operation and its entire dependency closure pass. This is the primary metric of the paper.
- **LHCR-All** = 1 iff every operation passes, side operations included.

The paper averages them over workflows. `scoring/chain.py` is the only reader of these verdicts; `scoring/score_run.py` applies it to one trajectory file.

## Trajectories

Each file is one run: the brief the agent saw (`brief`, `system_prompt`), every tool call with its arguments and response (`trace`), the agent's final message, token usage, and the harness's per-operation verdicts (`per_node`, `final_state_verifier`). File names encode the setting and the model, for example `S3_plan_map_oracle__gpt-5.6-sol__<instance>.json`.

On the ten all-fail workflows every shipped S2 run has LHCR-Req = 0; the per-operation table printed by `score_run.py` shows where each chain broke. On the case-study workflow GPT-5.6 Sol fails S1–S3 and passes S4. `trajectories/case_study.md` walks through the S2 run: one narrowed reading of "approved loans" at a root step (65 → 3) flips the decision branch, and the agent then executes fifteen downstream steps consistently for a state that does not exist, including a self-reconciliation that never re-asks the book. The same run can be replayed step by step on the [project page](https://holayan.github.io/EnterpriseWorld_Benchmark/#workflow).

## Perturbations

Each variant under a workflow's `perturbations/` keeps the same world and gold answers and changes one thing, recorded in its `pert.json`; `manifest.json` indexes the variants of a workflow. The first two operators change the dependency topology; the other two change the task/tool surface while preserving the required dependency graph.

| variant | operator (paper name) | what changes |
|---|---|---|
| `bridge__k1`, `bridge__k3`, `bridge__k5` | Path deepening, k = 1 / 3 / 5 | the value on one required edge is relayed through k extra required operations, each with its own check |
| `gate__p3` | Prerequisite / fan-in, +3 | a required consumer gains three extra upstream operations it must wait for; its own value is unchanged |
| `distractor__d10` | Distractor branches, +10 | ten inactive conditional branches are added to the goal; their guards are never true, and firing one fails the run |
| `tool__x10` | Tool distractors, +10 | ten real, callable decoy tools are registered next to the five the task needs; graph, gold, and checks are untouched |

Each variant carries its own `g_exec.json`, `instance.json`, `overall_query_plan.txt`, and `s2_constraints.json`, so it is run and scored exactly like a base workflow.

## The case-study instance

A balance-transfer desk processes a cardholder's request. Twenty operations span nine systems under one SQLite connection (a bank account book, a CRM and calendar, a payments ledger, an expense splitter, e-mail, a task tracker, and an enterprise scheduler / ITSM / HR mirror). The dependency spine is depth 12: two root figures computed from the account book decide the transfer base and the promo uplift; those select a decision branch; the branch gates which handoff e-mail may be sent, what the ledger posts, how the CRM is stamped, which intake ticket is filed, and how the closing review is booked.

## World snapshots

Each workflow's initial world, `world_s0.sqlite.gz`, is the merged initial state of the upstream databases (100–150 tables, about a million rows, most of it the untouched bulk of those databases), 22–163 MB compressed per workflow. The snapshots are not kept in git. Download the archive (link: TBD) and place each file as `instance/<instance>/world_s0.sqlite.gz`. Scoring the shipped trajectories does not need the world; it is needed only to run a new agent.

## Data sources and licence

The world merges public datasets under table prefixes: BIRD `financial` (`bird_*`), WorkBench (`wb_*`), AppWorld base databases (`vm_*`, `sw_*`, `gm_*`, `td_*`, `sn_*`), and EnterpriseOps-Gym (`eops_*`). Root questions inherit those datasets' own gold queries verbatim; every organisation, person, and address in the scenario layer is fictional. Redistribution follows the upstream licences; see `DATA_SOURCES.md`.

## Citation

```bibtex
@inproceedings{liu2027enterpriseworld,
  title     = {EnterpriseWorld: A Realistic World for Enterprise Long-Horizon Agents},
  author    = {Liu, Hongjun and Pang, Bo and Ming, Yifei and Koul, Anurag and Pakhomov, Egor and Zhao, Chen and Joty, Shafiq and Nijkamp, Erik},
  booktitle = {Under review},
  year      = {2027}
}
```
