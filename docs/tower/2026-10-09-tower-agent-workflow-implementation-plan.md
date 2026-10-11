# Tower Agent Workflow Implementation Plan

> **For agentic workers:** Use the installed `swarm-cluster` skill for approved parallel work, or follow the current environment's in-session plan execution workflow. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add three globally discoverable, model-agnostic Tower agents that coordinate adaptive routing and a requirements-to-delivery engineering loop.

**Architecture:** Add one primary `tower-controller` agent and two subagents identified by model capability tier: `tower-high-capability` and `tower-lightweight`. The controller handles routing and handoffs; every new Feature and other high-difficulty task defaults to high-capability Spec/Plan followed by lightweight Build/Test/Fix/Retest, while easy non-Feature work can be completed end-to-end by the lightweight agent.

**Tech Stack:** OpenCode V2 Markdown agent definitions with YAML frontmatter; existing Superpowers skills; OpenChamber model binding configured by the user later.

**Spec:** `docs/tower/2026-10-09-tower-agent-workflow-design.md`

## Global Constraints

- Create only `~/.config/opencode/agents/tower-controller.md`, `tower-high-capability.md`, and `tower-lightweight.md`.
- Use V2 frontmatter fields (`description`, `mode`, `permissions`); do not copy legacy `permission`, `tools`, or `temperature` fields from older local definitions.
- Do not include a `model` field; OpenChamber model binding is user-managed.
- Controller is `mode: primary`; the two tier agents are `mode: subagent`.
- High-capability and lightweight identify model tiers, not fixed Plan/Build job titles.
- New Features and other high-difficulty tasks default to high-capability Spec/Plan, then lightweight Build/Test/Fix/Retest; easy non-Feature tasks may be completed end-to-end by the lightweight agent.
- Progress reports are informational; do not wait for routine user approval between stages. The user audits the completed loop.
- Preserve existing agents, `AGENTS.md`, `opencode.jsonc`, default agent, and all unrelated files. Do not commit or push.

## Review Focus

- A small/new Feature and every other high-difficulty task must route through high-capability Spec/Plan, then lightweight Build/Test/Fix/Retest.
- A lightweight agent must be allowed to reason and finish a simple task end-to-end, not only execute code edits.
- The high-capability agent must not be constrained to planning-only duties.
- The controller must not implement code and may invoke only the two named tier agents.
- Omitting `model` means runtime model behavior cannot be verified until OpenChamber is configured; report this limitation rather than claiming model-level validation.

---

### Task 1: Add the Two Model-Tier Agents

**Files:**
- Create: `agents/tower-high-capability.md`
- Create: `agents/tower-lightweight.md`
- Reference: `docs/tower/2026-10-09-tower-agent-workflow-design.md`

**Interfaces:**
- Consumes: approved Tower roles, routing rules, progress behavior, Superpowers mapping, and handoff contract in the Spec.
- Produces: OpenCode subagent IDs `tower-high-capability` and `tower-lightweight`.
- Both omit `model`; the user binds model tiers in OpenChamber.

- [x] **Step 1: Create `tower-high-capability.md`**
  - Use V2 frontmatter with `description` and `mode: subagent`; omit `model`.
  - Define its default new-Feature brainstorming, detailed Spec, and Plan responsibilities without restricting it to planning-only work.
  - Define structured handoff fields and relevant Superpowers use.

- [x] **Step 2: Create `tower-lightweight.md`**
  - Use V2 frontmatter with `description` and `mode: subagent`; omit `model`.
  - Define independent reasoning and end-to-end completion of simple non-Feature tasks.
  - For routed implementation work, define Build/Test/Fix/Retest, scope adherence, and evidence reporting.

- [x] **Step 3: Verify both tier agents load**
  - Run `opencode debug agents --log-level debug --print-logs`.
  - Expected: both IDs appear with `mode: subagent`, and neither has a model assignment.

### Task 2: Add the Tower Controller

**Files:**
- Create: `agents/tower-controller.md`

**Interfaces:**
- Consumes: the two tier-agent IDs from Task 1 and the shared handoff protocol in the Spec.
- Produces: OpenCode primary-agent ID `tower-controller`.
- May invoke only `tower-high-capability` and `tower-lightweight`; does not implement code itself.

- [x] **Step 1: Create the V2 primary-agent definition**
  - Use `mode: primary`; omit `model`.
  - Use V2 `permissions` rules to deny direct `edit` and `shell`, deny arbitrary subagent calls, and allow only the two named tier agents.

- [x] **Step 2: Encode routing and process management**
  - Every new Feature routes through high-capability Brainstorm/Spec/Plan, then lightweight Build/Test/Fix/Retest.
  - Easy non-Feature work may route directly to the lightweight agent; complex/high-risk work routes through high-capability Plan and lightweight Build/Test/Fix/Retest by default, while Tower may assign additional duties to the high-capability agent as appropriate.
  - Track phase, owner, next action, dependencies, artifacts, and blockers; report milestones in the conversation and continue without routine approval requests.
  - Deliver final evidence and unresolved items for the user's audit after the loop completes.

### Task 3: Integrated Definition and Routing Verification

**Files:**
- Read: the three new Tower agent definitions.
- Create/run: `tests/2026-10-09-tower-agent-config-smoke-test.py`.

- [x] Run `opencode debug agents --log-level debug --print-logs` and confirm all three IDs and expected modes are present.
- [x] Add an executable smoke test for runtime discovery, ordered routing/fallback markers, model-agnostic definitions, and controller permissions; explicitly exclude model-backed behavior.
- [x] Inspect the loaded definitions for absent `model` fields and the controller's restricted subagent permissions.
- [x] Trace four routing cases against the prompts: a small new Feature, a simple existing bug, a complex non-Feature task, and a blocked test run. Confirm the routes and report/continue behavior match the Spec.
- [x] Confirm only the three planned global Agent definitions and the scoped, date-prefixed smoke test were added; no unrelated config, existing agent, commit, or push changes.
- [x] State that model-separated runtime delegation remains unverified until the user assigns models in OpenChamber.

## Execution Choice

Use the current session (Native): the three prompts share a single routing and handoff contract, so keeping their creation together reduces drift. Run one fresh-context `goal-verify` audit over the complete result afterward.
