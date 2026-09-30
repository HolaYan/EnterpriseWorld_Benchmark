# Upstream data

| prefix | source | what is used |
|---|---|---|
| `bird_*` | BIRD (dev split, `financial` database) | the tables verbatim; three root questions and their gold SQL |
| `wb_*` | WorkBench | CRM and calendar tables |
| `vm_*`, `sw_*`, `gm_*`, `td_*`, `sn_*` | AppWorld base databases | payments, expense splitting, e-mail, tasks, notes |
| `eops_*` | EnterpriseOps-Gym | scheduler, ITSM and HR databases with their native state verdicts |

Each is redistributed under its own licence; the scenario layer (CRM stamps, ledger tags, e-mail subjects, desk
notes, oracles) is original to this benchmark and fictional.
