# Long-horizon enterprise workflow benchmark — eleven instances, released for review

This repository holds **eleven complete instances** of the benchmark described in the submission, together with the
initial world state each runs on, their perturbation variants, real model trajectories with per-node verdicts, and
the scorer that reads them. It exists so reviewers can inspect real data, not a description of it. The full release
(200 instances, all models) follows publication.

Ten instances were chosen so that **every evaluated model fails them in the default setting (S2)**, one per
business-function category of the benchmark, all in an enterprise operations context; the eleventh
(`hybrid_balance_transfer_offer__0001`) is the case study walked through in `trajectories/case_study.md`.

| instance | category | depth | required / nodes | S2 trajectories (all fail) | variants |
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

Astra = GPT-6 Astra, Sol = GPT-5.6 Sol, Fable = Claude Fable 5.1 (evaluated on a 50-instance subset, hence present
on one of the ten), Opus = Claude Opus 4.8, Gemini = Gemini 3.7 Flash. Depth = longest dependency path; required =
the final task plus its dependency closure. Variants exist for the instances that were in the perturbation sweep.

Every instance directory has the same layout, shown here for the case-study instance:

```
instance/hybrid_balance_transfer_offer__0001/
  overall_query_detailed.txt   Setting 1 query: the goal with every step spelled out
  overall_query_plan.txt       Setting 2 query: the goal only; the agent plans the steps itself
  s2_constraints.json          desk notes — policy clauses the world surfaces just-in-time (Setting 2 and above)
  oracle_map.json              Setting 3 sidecar: Dependency-Map Oracle (which upstream steps constrain each consumer)
  oracle_handoff.json          Setting 4 sidecar: Handoff Oracle (the correct dependency object, delivered when needed)
  instance.json                agent_visible (query, world summary, conventions, tool list) + hidden (gold DAG, verifier)
  g_exec.json                  the executable 20-node DAG: R/W field sets, dependency edges, per-node verifiers, roles
  gt_trace.json                the gold trace: the figure each node writes and the SQL recipe that yields it
  world_s0.sqlite.gz           the merged initial world the agent acts on — downloaded separately, see below
  perturbations/               six variants of the same instance (bridge k=1/3/5, gate +3, distractor +10, tool +10)
trajectories/<instance>/       real runs with per-node verdicts: the S2 run of every model on the ten all-fail
                               instances; the four settings of GPT-5.6 Sol on the case-study instance
scoring/                       chain.py (the LHCR reader) and score_run.py (prints a trajectory's verdicts)
```

## World snapshots (download, not in the repository)

Each instance's initial world, `world_s0.sqlite.gz`, is the merged initial state of the upstream databases (100–150
tables, about a million rows, most of it the untouched bulk of those databases), 22–163 MB compressed per instance.
They are not kept in git; download the archive (link: TBD) and place each file as
`instance/<instance>/world_s0.sqlite.gz`. Scoring the shipped trajectories does not need the world — the per-node
verdicts are recorded in the files; the world is needed only to run a new agent.

## The case-study instance

A balance-transfer desk processes a cardholder's request. Twenty steps span nine systems under one SQLite
connection (a bank account book, a CRM and calendar, a payments ledger, an expense splitter, e-mail, a task tracker,
and an enterprise scheduler / ITSM / HR mirror). The dependency spine is depth 12: two root figures computed from
the account book decide the transfer base and the promo uplift; those select a decision branch; the branch gates
which handoff e-mail may be sent, what the ledger posts, how the CRM is stamped, which intake ticket is filed, and
how the closing review is booked. Every node is the tuple

```
(instruction, skills, tools, context, artifacts{A_in, A_out}, R, W, action_semantics, source, verifier, role)
```

`R` / `W` are field-level read and write sets; an edge `a → b` exists only where `W(a) ∩ R(b) ≠ ∅` on a shared
entity. `role` is `required` (the final task or one of its dependency ancestors) or `optional` (a side probe).
The `hidden` half of `instance.json` and the verifiers in `g_exec.json` are never shown to the agent.

## The four settings

| setting | what the agent receives | file |
|---|---|---|
| S1 detailed | the goal with every step written out | `overall_query_detailed.txt` |
| S2 plan | the goal only; policy clauses arrive as desk notes when the agent first touches the tables they govern | `overall_query_plan.txt` + `s2_constraints.json` |
| S3 = S2 + Dependency-Map Oracle | S2, plus for each consumer step which upstream steps constrain it and how (no values) | `oracle_map.json` |
| S4 = S2 + Handoff Oracle | S2, plus the correct dependency object handed over when the consumer needs it | `oracle_handoff.json` |

Oracles travel through the same desk-note channel as the policy clauses, so the trajectory records what was
delivered and when.

## Scoring

The world is scored **after** the run, on the saved final state. A node passes only if its own checks **and** every
dependency ancestor's checks pass (the closure verdict). Two numbers per run, both binary:

- **LHCR-Req** = 1 iff the final task and its entire dependency closure pass.
- **LHCR-All** = 1 iff every node passes, side probes included.

```
python3 scoring/score_run.py trajectories/hybrid_balance_transfer_offer__0001/S2_plan__gpt-5.6-sol__hybrid_balance_transfer_offer__0001.json
```

prints the two verdicts and a per-node table (own check / closure check / first failed check).

## The trajectories

Each file is one run: the brief the agent saw (`brief`, `system_prompt`), every tool call with its arguments and
response (`trace`), the agent's final message, token usage, and the harness's per-node verdicts (`per_node`,
`final_state_verifier`). On the ten all-fail instances every shipped S2 run has LHCR-Req = 0; the per-node table
printed by `score_run.py` shows where each chain broke. On the case-study instance GPT-5.6 Sol fails S1–S3 and passes S4. `trajectories/case_study.md`
walks through the S2 run: one narrowed reading of "approved loans" at a root step (65 → 3) flips the decision
branch, and the agent then executes fifteen downstream steps consistently for a state that does not exist,
including a self-reconciliation that never re-asks the book.

## Perturbations

Each variant under an instance's `perturbations/` keeps the same world and gold answers and changes one thing, recorded in
`pert.json`: **bridge** relays a value through k extra hand-off steps on one required edge; **gate** adds three
extra parents a required consumer must wait for; **distractor** adds ten inactive branches to the goal whose
ceilings are never reached; **tool** registers ten real, callable decoy tools next to the five the task needs.

## Reproducing a run

The agent operates through five tools over the SQLite world: `query` (read-only SELECT), `describe_table`,
`create_row`, `update_row`, `delete_row`. Decompress `world_s0.sqlite.gz`, expose those tools over the connection
to any agent, give it the setting's query, and score the resulting database with the verifiers in `g_exec.json`
(each is a SQL check with an expected value; the closure verdict composes them along `depends_on`). The harness
that does this for the models in the paper will be released with the full dataset.

## Data sources

The world merges public datasets under table prefixes: BIRD `financial` (`bird_*`), WorkBench (`wb_*`),
AppWorld base databases (`vm_`, `sw_`, `gm_`, `td_`, `sn_`), and EnterpriseOps-Gym databases (`eops_*`). Root
questions inherit those datasets' own gold queries verbatim; every organisation, person and address in the
scenario layer is fictional. Redistribution here follows the upstream licences; see `DATA_SOURCES.md`.
