# Tower Spec / Plan / Build / Review Workflow Implementation Plan

> **For agentic workers:** Use the installed `swarm-cluster` skill only for approved independent parallel work, or follow the current environment's in-session plan execution workflow. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a divergent-but-decisive Spec phase and review-gated, scope-bounded Plan/Build/Review flow to Tower's existing three-agent workflow.

**Architecture:** Keep `tower-controller`, `tower-high-capability`, and `tower-lightweight` and their current model-agnostic configuration. The controller adds pre-Build verdict routing and post-Build review; high-capability instructions define exploration, planning, and review contracts; lightweight instructions enforce the implementation boundary. The existing Python smoke test validates prompt markers and route ordering.

**Tech Stack:** OpenCode Agent Markdown prompts; Python 3 standard library; existing `opencode debug agents` discovery CLI. No new dependencies.

**Spec:** `docs/superpowers/specs/2026-10-10-tower-spec-plan-build-review-design.md`

## Global Constraints

- Apply the full workflow to every new Feature and any high-difficulty task routed through Spec/Plan; retain direct lightweight handling for clear, low-risk, non-Feature tasks.
- Do not add Agent IDs, model IDs, dependencies, or work-item states.
- Keep review verdicts separate from `queued`, `in_progress`, `blocked`, and `done`.
- Preserve Work ID tracking, the third-same-failure-fingerprint escalation, existing permissions, and progress reports as notifications rather than routine approval gates.
- Do not implement behavior beyond the original request without explicit user approval; block and ask if such behavior is necessary to proceed.
- Keep changes limited to the three approved Tower Agent files, the existing config smoke test, and the dated workflow design record.
- Do not stage, commit, or push. The AIWorkspace directory is not a Git repository; do not initialize Git or create a worktree for these changes.
- The Agent configuration files are outside the workspace and are explicitly part of the user-approved scope; do not write to any other global configuration path.
- Smoke-test success proves configuration discovery and prompt contracts only, not model-backed delegation.

## Review Focus

- `PASS_STANDARD` versus `PASS_HIGH_RISK` routing: pin lightweight versus high-capability Build to the matching verdict in the smoke test (Task 1).
- `REVISE` or `BLOCKED` before Build: pin that neither verdict can dispatch implementation in the controller route sequence (Task 1).
- Plan/file-scope adjustment versus new user-visible behavior: assert that behavior-preserving changes route through Tower/Plan while new behavior requires explicit user approval (Tasks 1 and 3).
- Post-Build findings that are defects versus out-of-scope ideas: assert omission scan, requirement traceability, and defer-only handling for out-of-scope ideas (Task 1).
- Regression of existing routing: keep the simple non-Feature direct route and third-failure escalation asserted in the existing smoke test (Task 1).

---

### Task 1: Add regression checks for the new Tower contracts

**Files:**
- Modify: `tests/2026-10-09-tower-agent-config-smoke-test.py`
- Read: `~/.config/opencode/agents/tower-controller.md`
- Read: `~/.config/opencode/agents/tower-high-capability.md`
- Read: `~/.config/opencode/agents/tower-lightweight.md`

**Interfaces:**
- Consumes: the existing `EXPECTED_MODES`, `REQUIRED_PROMPT_MARKERS`, `REQUIRED_PROMPT_SEQUENCES`, and `check_prompt_sequences(agent_id, prompt, failures)`.
- Produces: required markers and in-order prompt sequences for the approved review verdicts, Spec/Plan contracts, scope firewall, and dual-pass review. Preserve all existing assertions for model-agnostic configuration, permissions, simple non-Feature routing, Work IDs, and escalation.

- [x] **Step 1: Add controller markers and ordering checks** for `PASS_STANDARD`, `PASS_HIGH_RISK`, `REVISE`, and `BLOCKED`; assert the two pass verdicts map to the specified Agent tiers and the latter two cannot start Build. Add an ordered post-Build review sequence for omission/regression scanning, tracing every original requirement from Spec through implementation to test/verification evidence, and out-of-scope deferral.
- [x] **Step 2: Add high-capability markers and ordering checks** for `Diverge, Compare, Converge`, numbered requirement IDs, candidate trade-offs and selected approach, acceptance mapping, and separate-context review with evidence/disposition.
- [x] **Step 3: Add lightweight markers and ordering checks** for implementing only approved acceptance criteria, no silent scope expansion, behavior-preserving Plan updates, explicit approval for new user-visible behavior, and deferral of out-of-scope ideas.
- [x] **Step 4: Run the smoke test against the unmodified Agent prompts.**

Run: `python3 tests/2026-10-09-tower-agent-config-smoke-test.py`<br>
Expected: `Tower agent smoke test: FAIL` with missing new-contract markers/sequences and no Python syntax or OpenCode discovery error. Confirmed; Task 1 re-review passed after strengthening the evidence-traceability assertion.

### Task 2: Implement controller routing and high-capability reasoning/review contracts

**Files:**
- Modify: `~/.config/opencode/agents/tower-controller.md`
- Modify: `~/.config/opencode/agents/tower-high-capability.md`
- Test: `tests/2026-10-09-tower-agent-config-smoke-test.py`

**Interfaces:**
- Consumes: Task 1's new smoke-test markers and the approved Spec.
- Produces: controller route verdicts and high-capability Spec/Plan/review instructions used by Task 3's Builder contract.

- [x] **Step 1: Update `tower-controller.md`** to keep the original request as the baseline, record review verdict separately from work-item status, route `PASS_STANDARD` to `tower-lightweight`, route `PASS_HIGH_RISK` to `tower-high-capability`, send `REVISE` back to Spec/Plan without Build, and stop on `BLOCKED`. Require the post-Build omission/regression scan before requirement-to-evidence traceability. Route in-scope omissions/defects/regressions to focused Fix; route original-request requirements missing from Spec through Spec/Plan correction; defer out-of-scope ideas; and block/ask the user if new behavior beyond the original request is necessary. Preserve existing direct simple-task routing, progress policy, Work ID ledger, permissions, and escalation rule.
- [x] **Step 2: Update `tower-high-capability.md`** to produce numbered requirements; compare relevant alternatives and document trade-offs/selection; define scope, non-goals, and traceable acceptance criteria; turn these into ordered Plan tasks, target files, and verification. Define separate-context pre- and post-Build review assignments that scan relevant omissions and then trace original requirements to evidence; report findings and disposition without expanding scope. The prompt must not imply cross-model independence.
- [x] **Step 3: Run the smoke test to check the completed controller/high-capability contracts.**

Run: `python3 tests/2026-10-09-tower-agent-config-smoke-test.py`<br>
Expected: controller and high-capability markers/sequences pass; remaining failures, if any, are limited to Task 3's lightweight-owned markers. Confirmed; Task 2 reviewer approved spec compliance and quality.

### Task 3: Add the lightweight Build scope firewall

**Files:**
- Modify: `~/.config/opencode/agents/tower-lightweight.md`
- Test: `tests/2026-10-09-tower-agent-config-smoke-test.py`

**Interfaces:**
- Consumes: controller verdict routing and high-capability reviewed Spec/Plan from Task 2.
- Produces: a Builder contract that accepts only the approved scope and returns plan-change proposals to Tower.

- [x] **Step 1: Update `tower-lightweight.md`** to implement only approved acceptance criteria; prohibit new behavior, unrelated refactors, and drive-by cleanup; require reporting an infeasible plan or behavior-preserving file-scope change to Tower before proceeding; prohibit new user-visible behavior beyond the original request without explicit user approval; and report out-of-scope ideas as deferred.
- [x] **Step 2: Run the complete smoke test.**

Run: `python3 tests/2026-10-09-tower-agent-config-smoke-test.py`<br>
Expected: `Tower agent smoke test: PASS`; output continues to state that model-backed delegation is not tested. Confirmed; Task 3 reviewer approved spec compliance and quality.

### Task 4: Synchronize the dated Tower workflow record

**Files:**
- Modify: `docs/tower/2026-10-09-tower-agent-workflow-design.md`
- Read: `docs/superpowers/specs/2026-10-10-tower-spec-plan-build-review-design.md`

**Interfaces:**
- Consumes: the approved Spec and the implemented Agent contracts from Tasks 2–3.
- Produces: a dated `2026-10-11` supplement aligned with the operational config.

- [x] **Step 1: Append a dated `2026-10-11` supplement** recording the divergence/convergence contract, four pre-Build review verdicts and tier routing, Builder scope firewall, two-pass post-Build review, user-approval boundary for new behavior, and unchanged work-item states/third-failure escalation. Clarify that Build may implement approved user-visible behavior but not unapproved behavior beyond scope. Include the Spec path; do not rewrite or remove earlier decisions.
- [x] **Step 2: Read back the supplement** and check that it introduces no conflicting route, new Agent/model/status, or claim of real model delegation. Confirmed; the fresh Task 4 re-review approved the scope clarification.

### Task 5: Run an independent final audit

**Files:**
- Audit read-only: `~/.config/opencode/agents/tower-controller.md`
- Audit read-only: `~/.config/opencode/agents/tower-high-capability.md`
- Audit read-only: `~/.config/opencode/agents/tower-lightweight.md`
- Audit read-only: `tests/2026-10-09-tower-agent-config-smoke-test.py`
- Audit read-only: `docs/tower/2026-10-09-tower-agent-workflow-design.md`
- Audit read-only: `docs/superpowers/specs/2026-10-10-tower-spec-plan-build-review-design.md`

**Interfaces:**
- Consumes: all changed files and the smoke-test result.
- Produces: fresh-context audit verdict, findings by severity, and actual verification evidence.

- [x] **Step 1: Run the final smoke test** from a fresh audit context using the exact command from Task 3. It passed, validating configuration discovery and prompt contracts only.
- [x] **Step 2: Independently check** requirement completeness, verdict routing, scope-change behavior, existing route/escalation preservation, prompt/test consistency, and the explicit limitation on model-backed verification. The fresh `goal-verify` audit returned FAIL: 1 BLOCKER (incomplete post-Build rework loop) and 2 MAJOR (reviewer assignment and missing smoke assertions for the loop/assignment).
- [x] **Step 3: Add smoke-test assertions first** for `tower-high-capability` assignment to both pre- and post-Build reviews, Fix → verify → repeat independent two-pass review, and omitted-original-requirement → Spec/Plan revision → pre-Build re-review → Build remaining unmet acceptance criteria → verify → post-Build re-review. Run the exact smoke command and confirm a focused RED before changing prompts; a fresh Task 1 review approved the test coverage and expected failure.
- [x] **Step 4: Close the findings** in the Controller/high-capability prompts and the dated workflow supplement; preserve existing verdict/status/routing/escalation contracts. Run the smoke test to PASS and read back the changed workflow section. Task-level reviews approved the prompt and document fixes. One local run reported missing agents; direct CLI discovery then listed all three Tower agents and the exact smoke-test retry passed. The cause of that single discrepancy was not established.
- [x] **Step 5: Obtain a fresh read-only `goal-verify` audit** against the reworked state. Result: `CONDITIONAL PASS`; 1 MAJOR found—the smoke test did not assert that Spec-omission remediation waits for a passing pre-Build review before Build. The prompt already states this gate; the audit requests regression coverage.
- [x] **Step 6: Strengthen the smoke-test sequence** to assert `repeat the pre-Build review` → `wait for it to pass before Build` → `Build every remaining unmet approved acceptance criterion`. Demonstrate the sequence check fails against a synthetic prompt with the gate removed, then run the exact smoke test and confirm PASS. Fresh task review approved the assertion and negative probe.
- [x] **Step 7: Obtain a fresh read-only `goal-verify` audit PASS** against the final state. The third-round independent audit returned PASS with 0 BLOCKER, 0 MAJOR, and 1 MINOR (the earlier one-off missing-agent discovery result was not reproduced by the final smoke run). Do not stage or commit.
