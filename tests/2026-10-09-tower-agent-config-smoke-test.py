#!/usr/bin/env python3
"""Smoke-test loaded Tower agent routing and progress-management contracts.

This checks OpenCode discovery and prompt/config invariants; it does not run
an LLM or prove model-backed delegation behavior.
"""

import json
import subprocess
import sys
from pathlib import Path


COMMAND = ["opencode", "debug", "agents", "--log-level", "debug", "--print-logs"]
EXPECTED_MODES = {
    "tower-controller": "primary",
    "tower-high-capability": "subagent",
    "tower-lightweight": "subagent",
}
REQUIRED_PROMPT_MARKERS = {
    "tower-controller": (
        "任何新 Feature",
        "清楚、范围有限、低风险的非 Feature 任务",
        "其他高难度非 Feature 任务",
        "先从用户请求提取目标、范围、验收标准、风险和是否引入新行为，再选择路径",
        "通知，不是审批请求",
        "最终审计",
        "为每个可独立委派的子任务分配会话内唯一的 Work ID",
        "台账至少包含：Work ID、负责人、状态、依赖、验收标准/交付物、验证证据、下一步",
        "状态统一为 `queued`、`in_progress`、`blocked`、`done`",
        "每次派发、收到回报、阻塞、重新分配、返工或完成后，立即更新台账",
        "不得把没有交付物与验证证据的工作项标为 `done`",
        "只有核验到 Spec/Plan 中有可验证验收标准、任务依赖和测试方法，才能把该工作项标为 `done`",
        "Spec/Plan 阶段的验证证据是产物核验，不表示实现测试已执行",
        "只并行派发互不依赖的工作项",
        "多项并行时逐项跟踪，不能因一个子任务完成就把整批标为完成",
        "除该升级情形外，高能力 Agent 默认负责 Spec/Plan，轻量 Agent 默认负责 Build/Test/Fix/Retest",
        "按 Work ID 记录失败指纹（已知根因；尚未定位时用失败测试/命令和稳定错误现象）",
        "一次独立尝试指一轮实质性实现/修正及其对应验证；同一轮中重复出现的日志或报错只计一次",
        "同一失败指纹第 3 次失败，立即触发“显性监督失败”",
        "将负责人升级为 `tower-high-capability`，由高能力 Agent 接手根因分析和 Build/Fix/Retest",
        "高能力档位不可用时，停止轻量重复重试并将工作项标为 `blocked`",
        "对三步及以上的多阶段任务，用 `todowrite` 记录顶层阶段",
        "压缩或上下文交接时，必须保留当前台账",
        "交接只包含完成该子任务所需的最小上下文",
        "总体：{完成数}/{总数} 已完成；当前：{阶段}/{负责人}；阻塞：{事项或无}；下一步：{动作}",
        "`PASS_STANDARD`",
        "`PASS_HIGH_RISK`",
        "`REVISE`",
        "`BLOCKED`",
        "route Build to `tower-lightweight`",
        "route Build to `tower-high-capability`",
        "return to Spec/Plan",
        "do not start Build",
        "stop and report the blocker",
        "scan for relevant omissions and regressions",
        "trace each original requirement",
        "trace every original requirement from Spec through implementation to test/verification evidence",
        "out-of-scope ideas as deferred",
        "Before Build, assign `tower-high-capability` to review the Spec/Plan in a separate task/context",
        "After Build, assign `tower-high-capability` to perform the post-Build review in a separate task/context",
        "For an in-scope omission, defect, or regression, perform a focused Fix",
        "repeat the independent two-pass review",
        "When an original-request requirement is omitted from the Spec, revise the Spec/Plan",
        "Build every remaining unmet approved acceptance criterion",
        "Do not mark complete while any required criterion remains unmet",
    ),
    "tower-high-capability": (
        "Every new Feature, regardless of apparent size",
        "Do not assume that you only write plans.",
        "brainstorming",
        "Spec and an actionable Plan",
        "Work ID: echo the ID assigned by Tower in every progress update and final report.",
        "Status must be one of `in_progress`, `done`, or `blocked`.",
        "If Tower did not provide a Work ID, do not invent one or begin substantive work; report `blocked` to Tower",
        "The high-capability tier is usually assigned Spec/Plan, but an explicit `显性监督失败` escalation makes it the owner of root-cause analysis and Build/Fix/Retest.",
        "On escalation, inspect the handed-off failure signature, attempts, evidence and current artifacts; implement a fix and run relevant verification rather than returning only a plan.",
        "Diverge",
        "Compare",
        "Converge",
        "numbered requirement IDs",
        "relevant alternatives",
        "trade-offs",
        "selected approach",
        "acceptance criteria mapped to requirement IDs",
        "separate-context review",
        "for both pre-Build Spec/Plan review and post-Build implementation review",
        "does not guarantee a different underlying model; do not claim otherwise",
        "After a focused Fix is completed and verified, perform a fresh independent review",
        "evidence",
        "disposition",
    ),
    "tower-lightweight": (
        "complete it end-to-end",
        "new Feature or high-difficulty task",
        "without its required Spec/Plan",
        "return it to Tower",
        "systematic-debugging",
        "Work ID: echo the ID assigned by Tower in every progress update and final report.",
        "Status must be one of `in_progress`, `done`, or `blocked`.",
        "If Tower did not provide a Work ID, do not invent one or begin substantive work; report `blocked` to Tower",
        "In reports to Tower, include a concise failure signature, independently attempted fixes and evidence; repeated log lines within one attempt are not separate attempts.",
        "If Tower escalates the Work ID under `显性监督失败`, stop repeating the same fix strategy and hand off; do not continue low-tier retries unless Tower explicitly reassigns the work.",
        "implement only the approved acceptance criteria",
        "do not silently expand scope",
        "report behavior-preserving Plan changes to Tower",
        "explicit user approval before implementing new user-visible behavior",
        "defer out-of-scope ideas",
    ),
}
REQUIRED_PROMPT_SEQUENCES = {
    "tower-controller": (
        (
            "1. **任何新 Feature",
            "`tower-high-capability` 做头脑风暴、详细 Spec 和 Plan",
            "`tower-lightweight` 完成 Build/Test/Fix/Retest",
        ),
        (
            "2. **清楚、范围有限、低风险的非 Feature 任务**",
            "`tower-lightweight` 从分析到验证端到端完成",
        ),
        (
            "3. **其他高难度非 Feature 任务**",
            "`tower-high-capability` 深入分析并 Plan",
            "`tower-lightweight` Build/Test/Fix/Retest",
        ),
        (
            "Spec、Plan、Build、Test、Fix、Retest 等里程碑汇报是**通知，不是审批请求**",
            "继续下一个阶段",
            "不要问“要不要继续”",
        ),
        (
            "遇到测试失败时，继续推进系统化排查、修正和复测",
            "停止空转并报告具体阻塞",
        ),
        (
            "测试失败时，将对应工作项保持为 `in_progress` 或标为 `blocked`",
            "记录失败证据和修正尝试",
            "没有新的证据或进展时停止空转并报告真实阻塞",
        ),
        (
            "按 Work ID 记录失败指纹（已知根因；尚未定位时用失败测试/命令和稳定错误现象）",
            "一次独立尝试指一轮实质性实现/修正及其对应验证；同一轮中重复出现的日志或报错只计一次",
            "同一失败指纹第 3 次失败，立即触发“显性监督失败”",
            "将负责人升级为 `tower-high-capability`",
            "由高能力 Agent 接手根因分析和 Build/Fix/Retest",
            "高能力档位不可用时，停止轻量重复重试并将工作项标为 `blocked`",
        ),
        (
            "派发前先创建或更新对应工作项",
            "派发时必须带上 Work ID",
            "每次派发、收到回报、阻塞、重新分配、返工或完成后，立即更新台账",
            "收到子 Agent 回报后，先更新台账",
        ),
        (
            "压缩或上下文交接时，必须保留当前台账",
            "不要默认新建独立进度文档",
        ),
        (
            "`PASS_STANDARD`",
            "route Build to `tower-lightweight`",
        ),
        (
            "`PASS_HIGH_RISK`",
            "route Build to `tower-high-capability`",
        ),
        (
            "`REVISE`",
            "return to Spec/Plan",
            "do not start Build",
        ),
        (
            "`BLOCKED`",
            "stop and report the blocker",
        ),
        (
            "scan for relevant omissions and regressions",
            "trace every original requirement from Spec through implementation to test/verification evidence",
            "out-of-scope ideas as deferred",
        ),
        (
            "Before Build",
            "assign `tower-high-capability` to review the Spec/Plan in a separate task/context",
            "before any verdict-to-Builder route",
        ),
        (
            "After Build",
            "assign `tower-high-capability` to perform the post-Build review in a separate task/context",
            "before the existing two review passes",
        ),
        (
            "For an in-scope omission, defect, or regression",
            "perform a focused Fix",
            "verify the Fix",
            "repeat the independent two-pass review",
            "do not mark complete until the review passes",
        ),
        (
            "When an original-request requirement is omitted from the Spec",
            "revise the Spec/Plan",
            "repeat the pre-Build review",
            "wait for it to pass before Build",
            "Build every remaining unmet approved acceptance criterion",
            "verify the implementation",
            "repeat the post-Build two-pass review",
            "Do not mark complete while any required criterion remains unmet",
        ),
    ),
    "tower-high-capability": (
        (
            "Diverge",
            "Compare",
            "Converge",
            "numbered requirement IDs",
            "relevant alternatives",
            "trade-offs",
            "selected approach",
            "acceptance criteria mapped to requirement IDs",
            "separate-context review",
            "evidence",
            "disposition",
        ),
        (
            "perform it in a separate task/context",
            "for both pre-Build Spec/Plan review and post-Build implementation review",
            "does not guarantee a different underlying model; do not claim otherwise",
            "After a focused Fix is completed and verified",
            "perform a fresh independent review",
        ),
    ),
    "tower-lightweight": (
        (
            "If a new Feature or high-difficulty task arrives without its required Spec/Plan,",
            "return it to Tower for routing through the high-capability tier before implementation.",
        ),
        (
            "implement only the approved acceptance criteria",
            "do not silently expand scope",
            "report behavior-preserving Plan changes to Tower",
            "explicit user approval before implementing new user-visible behavior",
            "defer out-of-scope ideas",
        ),
    ),
}


def effective_permission(agent, action, resource):
    matches = [
        rule["effect"]
        for rule in agent.get("permissions", [])
        if rule.get("action") in ("*", action)
        and rule.get("resource") in ("*", resource)
    ]
    return matches[-1] if matches else None


def check_prompt_sequences(agent_id, prompt, failures):
    for sequence_number, markers in enumerate(REQUIRED_PROMPT_SEQUENCES.get(agent_id, ()), 1):
        cursor = 0
        for marker in markers:
            position = prompt.find(marker, cursor)
            if position == -1:
                failures.append(
                    f"{agent_id}: sequence {sequence_number} missing or out of order at {marker!r}"
                )
                break
            cursor = position + len(marker)


def main():
    loaded = json.loads(
        subprocess.check_output(COMMAND, cwd=Path(__file__).resolve().parent, text=True)
    )
    agents = {agent["id"]: agent for agent in loaded}
    failures = []

    for agent_id, mode in EXPECTED_MODES.items():
        agent = agents.get(agent_id)
        if agent is None:
            failures.append(f"missing agent: {agent_id}")
            continue
        if agent.get("mode") != mode:
            failures.append(f"{agent_id}: expected mode {mode}, got {agent.get('mode')}")
        if "model" in agent:
            failures.append(f"{agent_id}: model must remain unassigned")
        prompt = agent.get("system", "")
        for marker in REQUIRED_PROMPT_MARKERS[agent_id]:
            if marker not in prompt:
                failures.append(f"{agent_id}: missing routing marker {marker!r}")
        check_prompt_sequences(agent_id, prompt, failures)

    controller = agents.get("tower-controller", {})
    for action, resource, expected in (
        ("edit", "*", "deny"),
        ("shell", "*", "deny"),
        ("subagent", "*", "deny"),
        ("subagent", "tower-high-capability", "allow"),
        ("subagent", "tower-lightweight", "allow"),
    ):
        actual = effective_permission(controller, action, resource)
        if actual != expected:
            failures.append(
                f"controller permission {action}/{resource}: expected {expected}, got {actual}"
            )

    if failures:
        print("Tower agent smoke test: FAIL")
        print("\n".join(f"- {failure}" for failure in failures))
        return 1

    print("Tower agent smoke test: PASS")
    print("Three agents load with expected modes, route order, progress tracking, and controller permissions.")
    print("Model-backed delegation is not tested; model binding remains the user's OpenChamber step.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
