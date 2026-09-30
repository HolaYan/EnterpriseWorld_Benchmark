# Case study — `hybrid_balance_transfer_offer__0001`, GPT-5.6 Sol, Setting 2 (plan)

Run: `trajectories/hybrid_balance_transfer_offer__0001/S2_plan__gpt-5.6-sol__hybrid_balance_transfer_offer__0001.json`
(162 tool calls, `stopped: done`, agent reports "completed and reconciled"). One misread at a root lookup; 15 of 17
required steps end up wrong on their own checks; LHCR-Req = 0. Chosen because the failure is a *consequence*, not a slip:
the agent executed the entire downstream workflow consistently for a state that did not exist.

## Panel 1 — Environment

| system | tables | role |
|---|---|---|
| Reference book (BIRD `financial`) | `bird_loan`, `bird_account`, `bird_client`, `bird_disp`, `bird_district`, `bird_trans` | root figures: portfolio balance, promo-window uplift, decision bars, side question |
| Workbench | `wb_customer_relationship_manager_data`, `wb_calendar_events` | BT-ops manager CRM stamps, review booking |
| Venmo | `vm_transactions` | payoff ledger `[BTO-XFER]` |
| Splitwise | `sw_expenses`, `sw_expense_shares`, `sw_payments` | fee allocation, underwriting settle-up |
| Gmail | `gm_emails` | underwriting handoff `[BTO-HANDOFF]`, manager status `[BTO-STATUS]` |
| Todoist | `td_tasks`, `td_task_comments` | reconciliation follow-up, wrap-up |
| EnterpriseOps calendar / ITSM / HR | `eops_gym_calendar_*`, `eops_gym_itsm_mcp_*`, `eops_sn_hr_internal_*` | promo-window hold, card-servicing intake, manager briefing case |

Query (Setting 2, abridged): *"Process the cardholder's balance-transfer request: the new promo-APR line pays off the
high-APR source card. Plan and carry the engagement out end to end yourself … DELIVERABLE: REPORT branch · delta ·
promo_uplift · reconciled · side_scan_count · source_balance · total_transfer · transfer_base."*

Desk note delivered at call #47 (when the agent first worked the loan book): *"The promo-window uplift is the count of
approved loans of at least 250,000 written between 1/1/1995 and 12/31/1997 on accounts with monthly statement
issuance"*, the two decision bars (conditional-review floor = distinct Pisek-district accounts with household-payment
transactions; decline bar = average running-contract loan / 200), and the branch rule.

## Panel 2 — Dependency-chained workflow (required chain)

```
n01 [1] source_balance  = avg loan amount over male borrower links ──▶ n02 [2] transfer_base = round(S/200) = 748 (CRM [BTO-BASE])
n03 [1] promo_uplift    = count of qualifying loans in the book   ──▶ n04 [3] total_transfer = base + uplift; delta = uplift
n04 ──delta, transfer_base──▶ n05 [4] branch: DECLINED if delta ≥ 100 or base ≥ decline bar; CONDITIONAL_UW_REVIEW if
                                       delta ≥ conditional floor and base ≥ 200; else AUTO_APPROVE_STANDARD_PROMO
n04 ──total_transfer──▶ n06 [4] promo-window hold in the enterprise scheduler      n04 ──delta──▶ n10 [4] fee allocation (Splitwise)
n05, n04 ──branch, figures──▶ n08 [5] [BTO-HANDOFF] e-mail to the underwriting desk — ONLY on conditional / declined
n08 ──subject──▶ n09 [6] CRM log [BTO-LOG] total_transfer — on conditional/declined only after the handoff
n09 ──▶ n11 [7] follow-up task [BTO-FUP] delta ──▶ n12 [8] re-derive the tier from the live book → CRM status [BTO-TIER]
n12 ──▶ n13 [9] card-servicing intake ticket gated on tier and base ──▶ n14 [10] [BTO-STATUS] e-mail citing total and tier
n14 ──▶ n15 [11] manager-briefing case reassigned, gated on the status e-mail and branch ──▶ n17 [12] [BTO-WRAP] comment
n10 ──▶ n16 [5] underwriting settle-up payment            n06, n15 ──▶ n19 [12] [BTO-REVIEW] booking, conflict-free
```
Two root lookups feed everything: the branch decision, the ledger amount, which e-mails may be sent, the tier stamp,
the intake ticket, the briefing hand-over, the wrap-up figure. Depth 12, three systems' worth of gated writes.

## Panel 3 — What the agent did

```
#52  query   avg loan amount over male-borrower links → source_balance = 149 609.18, transfer_base = 748          ✓
#53  query   SELECT COUNT(*) FROM bird_loan l JOIN bird_account a … WHERE l.status='A' AND l.amount>=250000
             AND l.date BETWEEN '1995-01-01' AND '1997-12-31' AND a.frequency='POPLATEK MESICNE'   → 3
             the book's own count has no status filter ("approved" = every loan the book holds)     → 65          ✗
#54  query   conditional-review floor (Pisek household-payment accounts)                                          ✓
     →  delta = 3 (< floor)  ⇒  branch = AUTO_APPROVE_STANDARD_PROMO      (gold: delta 65 ⇒ CONDITIONAL_UW_REVIEW)
#107 create  vm_transactions      [BTO-XFER] delta=3            payoff wired for 3 instead of 65
     (no e-mail to uw.review)      correct for its branch: on auto-approve the handoff MUST NOT be sent
#110 create  gm_emails            [BTO-STATUS] AUTO_APPROVE_STANDARD_PROMO … total_transfer=751
#111 create  td_tasks             [BTO-FUP] delta=3
#112 create  wb_calendar_events   [BTO-REVIEW] src_bal=149609.18, 14:00 slot after the window
#113–#118    enterprise scheduler: promo-window calendar, ACLs, watch channel
#119–#120,#125–#126  ITSM intake ticket re-filed; HR briefing case reassigned (gated on the auto-approve route)
#122 create  td_task_comments     [BTO-WRAP] transfer_total=751
#123 update  CRM                  status '[BTO-TIER] AUTO_APPROVE_STANDARD_PROMO promo_uplift=3', notes [BTO-RECON] delta=3 …
#132–#162    re-reads every ledger and record, confirms they agree with each other, reports reconciled: ok
```
REPORT: branch AUTO_APPROVE_STANDARD_PROMO · delta 3 · promo_uplift 3 · total_transfer 751 · reconciled ok
(gold: CONDITIONAL_UW_REVIEW · 65 · 65 · 813 · ok). Four of eight values wrong; the run is internally consistent.

## Panel 4 — Why it failed, and what it cost

- **Origin (one clause):** at n03 the agent added `l.status = 'A'` to the qualifying-loan count, reading "approved" as
  the loan table's status code; the book's question (BIRD `financial` #136, inherited verbatim by the verifier) counts
  every loan meeting the amount, date and issuance conditions. 65 became 3.
- **Propagation (15 steps, all executed, all wrong for the true state):** delta 65 → 3 crosses the conditional-review
  floor downward, so the branch flips from CONDITIONAL_UW_REVIEW to AUTO_APPROVE. From there every gated action is the
  *other* route's action: the payoff is wired for 3, the underwriting handoff that ratifies the payoff is not sent, the
  CRM log is written without the handoff, the tier stamp and status e-mail say AUTO_APPROVE, the briefing case is
  reassigned on that basis, the wrap-up quotes 751. Each step is correct relative to the agent's own state and wrong
  relative to the case's state; 15 of 17 required nodes fail their own checks (none merely blocked), including the final
  review booking whose pins require the true uplift, total, delta and branch.
- **Self-check did not catch it:** the reconciliation at #132–#162 re-derived the chain from the agent's own recorded
  figures and the ledger it had itself posted, so everything "netted"; nothing re-asked the book.
- **In the paper's vocabulary:** a producer error at depth 1 (state-sensitive: the value selects the branch), carried
  through eleven correct handoffs into a wrong branch and a wrong ledger amount — the compounding that turns a flat A(d)
  into a falling S(d). Same instance under the handoff oracle (S4, `trajectories/hybrid_balance_transfer_offer__0001/S4_plan_handoff_oracle__…json`): the oracle
  supplies uplift = 65 at n04 and the run passes.

Caveat: the disagreement is about what "approved loans" means in the reference book; the verifier holds
the book's own reading, which the desk note repeats, and the agent's narrower reading is the kind of semantic drift the
benchmark scores as a producer error.
