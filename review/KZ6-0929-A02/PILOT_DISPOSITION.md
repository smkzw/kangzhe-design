# A01 12-run pilot disposition

| Case | Native model | Result |
|---|---|---|
| codebuddy-H1-D01 | deepseek-v4.1-flash | FAIL: two Gantt durations, chart annotation overlap; upstream quick route not explicitly requested |
| codebuddy-H1-D02 | deepseek-v4.1-flash | FAIL: orange progress bar; H1 includes one repair |
| codebuddy-H1-D03 | deepseek-v4.1-flash | FAIL: red null annotation overlap and narrow-screen card overlap |
| codebuddy-H2-D01 | deepseek-v4.1-flash | PARTIAL: six Gantt intervals corrected; native Mac edit/readback not run for this exact artifact; quick route issue |
| codebuddy-H2-D02 | deepseek-v4.1-flash | FAIL: blue progress bar; footer contrast self-report below target |
| codebuddy-H2-D03 | deepseek-v4.1-flash | PARTIAL: parent EGO geometry/interaction checked; worker EGO blocked by shared page budget; mobile header wraps |
| pi-H1-D01 | gpt-6-luna | FAIL: no target PPTX at budget boundary |
| pi-H1-D02 | gpt-6-luna | FAIL: partial HTML with 10 missing HTTP dependencies, owner budget stop |
| pi-H1-D03 | gpt-6-luna | FAIL: no HTML, owner budget stop |
| pi-H2-D01 | gpt-6-luna | FAIL: no PPTX, owner budget stop |
| pi-H2-D02 | gpt-6-luna | FAIL: no target HTML, runner budget exhaustion |
| pi-H2-D03 | gpt-6-luna | FAIL: partial HTML, missing QC and handoff at budget boundary |

All 12 real calls are terminal. File-bearing output is not success. Runner nested recovery can exceed the declared 1800-second total; three specific progressing processes were stopped at discovery and preserved in OWNER_BUDGET_STOP.json. Timing/repair comparisons are confounded. No brand-based model capability conclusion, no synthetic model outputs, no 36-run expansion.

Blind review: pilot-blind-01, -02, -03; source/pixel disagreements remain in final-qc/JUDGE_ARBITRATION.md. Reviewer numerical scores are not a clean paired cross-track or dynamic assessment. Coordinator repairs live outside the pilot directories.
