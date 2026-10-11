# Tower Spec / Plan / Build / Review Workflow Design

Date: 2026-10-10<br>
Status: Approved by user on 2026-10-10; implementation plan drafted separately

## Goal

Improve Tower's feature-delivery workflow so that high-capability reasoning explores relevant possibilities and selects a solution, while planning, implementation, and review remain bounded by the original request and the selected solution. The workflow must catch omissions without turning review into silent scope expansion.

## Applicability

- Require this workflow for every new Feature and any high-difficulty task that Tower routes through Spec/Plan.
- Preserve the direct end-to-end lightweight route for clear, low-risk, non-Feature tasks.

## Existing baseline

- `tower-controller` coordinates work and does not implement code.
- `tower-high-capability` normally handles feature brainstorming, Spec, and Plan.
- `tower-lightweight` normally handles planned Build/Test/Fix/Retest.
- After the third independent failure with the same Work ID and failure fingerprint, responsibility escalates to `tower-high-capability` for root-cause analysis and Build/Fix/Retest.
- Work item states remain `queued`, `in_progress`, `blocked`, and `done`; `done` requires a deliverable and actual verification evidence.
- Routine stage reports are progress notifications, not user approval gates. Genuine blockers and safety/authorization boundaries remain exceptions.

## Design decisions

1. Keep the existing three Tower agents. Do not add agent IDs, model IDs, dependencies, or work-item states.
2. Treat Spec as **diverge, compare, and converge**: explore relevant scenarios, edge cases, risks, and alternative approaches; record trade-offs and select one recommended solution. Exploration does not make every idea part of scope.
3. Treat Plan as a **scope and execution contract**: map requirements to acceptance criteria and ordered tasks, dependencies, target files, verification, and explicit non-goals.
4. Add a pre-Build review. `tower-high-capability` performs the review as a separate task/context; it is role-separated, not a guarantee of cross-model independence.
5. Record review verdict separately from the four work-item states:
   - `PASS_STANDARD`: requirements and plan are complete, testable, and within manageable risk; route Build to `tower-lightweight`.
   - `PASS_HIGH_RISK`: the Spec/Plan is complete and actionable, but task complexity/risk warrants the high-capability tier for Build.
   - `REVISE`: a material gap, ambiguity, contradiction, or unresolved major risk remains; revise Spec/Plan and review again. Do not start Build.
   - `BLOCKED`: essential input, authorization, dependency, or environment is missing and cannot be safely assumed; stop and report the blocker.
6. Keep a scope firewall around Build. Implement only approved acceptance criteria. A necessary implementation/file-scope adjustment that preserves approved behavior is proposed to Tower; the high-capability tier updates Spec/Plan before implementation resumes. New user-visible behavior beyond the original request is never approved internally: do not implement it without explicit user approval. If it is necessary to proceed, mark the work blocked and ask the user. Local implementation choices that do not alter agreed behavior remain with the Builder.
7. Review after Build has two passes: (a) scan relevant edge cases, omissions, and regressions; (b) trace each original requirement through Spec acceptance criteria to implementation and test/verification evidence. Review findings must include evidence and disposition.
8. Route findings by meaning: an in-scope omission, implementation defect, or regression goes to focused Build/Fix; a requirement from the original request omitted from Spec first goes through Spec/Plan correction; an out-of-scope improvement is recorded/deferred, not implemented silently.
9. Keep the existing third-failure escalation rule unchanged. Review verdicts and escalation events are metadata on the Work ID, not new work-item states.
10. Preserve current model-agnostic routing and permissions. Do not hardcode model names or claim real delegated behavior verified while model bindings are unavailable.

## Phase contracts

### Spec — divergent exploration with a selected outcome

The Spec records:

- numbered requirements derived from the original request;
- relevant users/scenarios, edge cases, constraints, assumptions, and risks;
- candidate approaches with concise trade-offs and a clear selected approach;
- explicit in-scope items, non-goals, and deferred/out-of-scope ideas;
- testable acceptance criteria mapped to requirement IDs.

### Plan — convergent, executable constraints

The Plan records:

- ordered tasks and dependencies, using Work IDs where work is independently delegated;
- target files/artifacts and allowed scope;
- links from each task to requirement/acceptance IDs;
- verification commands or procedures and expected evidence;
- explicit prohibited scope expansion and the handoff procedure for proposed changes.

### Build — bounded execution

The assigned Builder receives the original request baseline, reviewed Spec/Plan, Work ID, its exact assignment, and verification requirements. It does not add product behavior, unrelated refactors, or drive-by cleanup. If the plan proves infeasible or an implementation/file-scope adjustment is necessary, it reports the reason and proposed change to Tower before proceeding. Tower may route a behavior-preserving Plan update back to the high-capability tier; behavior beyond the original request requires explicit user approval before it is added to Spec/Plan or implemented.

### Review — broad discovery, scope-anchored judgment

The reviewer first scans for relevant omissions and regressions, then checks traceability from original request to Spec, acceptance criteria, implementation, and evidence. Findings identify the requirement/acceptance link where applicable, concrete evidence, impact, and disposition. Unrelated pre-existing issues and useful-but-out-of-scope ideas are not treated as failures of this change.

## Routing and loop behavior

```text
New Feature
  -> high-capability Spec (diverge, choose, define scope)
  -> high-capability Plan (converge to bounded tasks)
  -> high-capability pre-Build review
       PASS_STANDARD -> lightweight Build/Test/Fix
       PASS_HIGH_RISK -> high-capability Build/Test/Fix
       REVISE -> update Spec/Plan -> review again; no Build yet
       BLOCKED -> stop and report required recovery input
  -> high-capability post-Build review
       in-scope omission/defect/regression -> focused Fix and re-review
       original-request requirement omitted from Spec -> update Spec/Plan, then Build
       out-of-scope improvement -> defer; do not expand implementation
       new behavior beyond original request needed to proceed -> block and ask user
  -> completion report with artifacts and actual verification evidence
```

The existing same-failure-fingerprint third-attempt escalation still applies to Build/Fix/Test work. Repeated work without new evidence or progress must stop and be reported as a blocker rather than loop indefinitely.

## Implementation scope

- Update `~/.config/opencode/agents/tower-controller.md` with the review gates, verdict-to-tier routing, and review/fix handoffs.
- Update `~/.config/opencode/agents/tower-high-capability.md` with Spec/Plan output contracts and the structured review task/report.
- Update `~/.config/opencode/agents/tower-lightweight.md` with Build scope boundaries, change proposals, and evidence requirements.
- Extend `tests/2026-10-09-tower-agent-config-smoke-test.py` to check the new contracts and routes.
- Append a dated supplement to `docs/tower/2026-10-09-tower-agent-workflow-design.md` so the operational record stays aligned.
- Do not stage, commit, or push.

## Acceptance criteria

1. Feature Spec instructions explicitly require relevant divergence, comparison, a justified selection, numbered requirements, scope/non-goals, and testable acceptance mapping.
2. Plan instructions require ordered, traceable, bounded tasks with file scope and verification evidence.
3. Pre-Build verdicts route `PASS_STANDARD` to lightweight Build and `PASS_HIGH_RISK` to high-capability Build; `REVISE` and `BLOCKED` cannot start Build.
4. Build instructions prohibit silent behavior/scope expansion and define the proposal → Spec/Plan update → resume path.
5. Post-Build review requires both a relevant omission/regression scan and original-request-to-evidence traceability; findings have a clear in-scope/out-of-scope disposition.
6. The existing four work-item states, Work ID tracking, third-failure escalation, model-agnostic configuration, no-routine-user-approval behavior, and direct lightweight route for simple non-Feature work remain intact.
7. The Tower config smoke test verifies the rules above and passes after implementation.
8. Configuration smoke-test success is not described as proof of real model delegation; that requires model bindings and a controlled run.

## Verification

- Run `python3 tests/2026-10-09-tower-agent-config-smoke-test.py`.
- Inspect the changed configuration and dated design supplement against the acceptance criteria.
- Report real model-delegation verification as unavailable unless model bindings are configured and exercised.

## Non-goals

- No dedicated Reviewer Agent or additional model binding.
- No changes to unrelated global instructions, existing agents, permissions, model IDs, dependencies, or work-item states.
- No silent implementation of ideas discovered during Spec or Review. Behavior beyond the original request requires explicit user approval; otherwise defer it or report a blocker if it is necessary to proceed.
- No commit or push.
