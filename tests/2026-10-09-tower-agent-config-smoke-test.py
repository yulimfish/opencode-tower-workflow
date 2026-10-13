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
AGENT_SOURCE_DIR = Path(__file__).resolve().parents[1] / "agents"
EXPECTED_MODES = {
    "tower-controller": "primary",
    "tower-high-capability": "subagent",
    "tower-lightweight": "subagent",
}
REQUIRED_PROMPT_MARKERS = {
    "tower-controller": (
        "先从用户请求提取目标、范围、验收标准、风险和依赖，再由你按任务实际所需的推理深度选择能力档位",
        "轻量工作默认交给 `tower-lightweight`",
        "调研、资料检索、事实核查、信息整理",
        "只有确实需要深度推理时才使用 `tower-high-capability`",
        "任务类别或风险标签本身都不自动升档",
        "新 Feature 按实际推理深度路由",
        "简单且范围明确的 Feature 交给 `tower-lightweight`",
        "高风险但无需深度推理的工作仍用轻量档",
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
        "高能力档仅在任务确需深度推理时使用，轻量 Agent 默认承担其余工作",
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
        "仅当 Build 确需深度推理时 route to `tower-high-capability`",
        "普通 Build/Test/Fix/Retest 的首轮都交给轻量档",
        "任务复杂、高风险、Plan 曾由强模型编写，或要求独立审计，都不单独构成首轮升档理由",
        "同一 Work ID、同一失败指纹累计到第 3 次独立失败后",
        "评审的**上下文独立性**与**模型档位**是两个决定",
        "要求 fresh context 或两遍审计本身不等于必须用强模型",
        "范围窄、标准清晰、低风险的审计可交给 `tower-lightweight`",
        "只有审计本身确需深度安全/领域推理，或轻量审计无法给出有证据的结论时",
        "首轮 Build 仍 route to `tower-lightweight`",
        "高风险 verdict 不绕过轻量首轮",
        "return to Spec/Plan",
        "do not start Build",
        "stop and report the blocker",
        "按核查所需推理深度选择 Agent",
        "只有确需深度推理时才用 `tower-high-capability`，否则用 `tower-lightweight`",
        "先查遗漏、缺陷和回归",
        "逐项追踪原始需求、验收标准、实现及测试/验证证据",
        "范围外想法记为 deferred",
        "按评审所需推理深度选择 Agent",
        "标准评审用 `tower-lightweight`",
        "For an in-scope omission, defect, or regression, perform a focused Fix",
        "repeat the independent two-pass review",
        "When an original-request requirement is omitted from the Spec, revise the Spec/Plan",
        "Build every remaining unmet approved acceptance criterion",
        "Do not mark complete while any required criterion remains unmet",
    ),
    "tower-high-capability": (
        "Features Tower routes to you for deep design reasoning",
        "Do not infer a need for high-tier work from the Feature label or size alone",
        "Reasoning Discipline",
        "precise, decision-relevant breadth and depth—not sheer volume",
        "Be comprehensive about relevant dimensions, not exhaustive for its own sake",
        "Do not repeat unchanged reasoning",
        "materially reduce uncertainty",
        "Do not assume that you only write plans.",
        "brainstorming",
        "Spec and an actionable Plan",
        "Work ID: echo the ID assigned by Tower in every progress update and final report.",
        "Status must be one of `in_progress`, `done`, or `blocked`.",
        "If Tower did not provide a Work ID, do not invent one or begin substantive work; report `blocked` to Tower",
        "The high-capability tier is usually assigned Spec/Plan, but an explicit `显性监督失败` escalation makes it the owner of root-cause analysis and Build/Fix/Retest.",
        "On escalation, inspect the handed-off failure signature, attempts, evidence and current artifacts; implement a fix and run relevant verification rather than returning only a plan.",
        "Build routing guard",
        "evidence of the third independent failure",
        "return the assignment to Tower for the lightweight first-pass route",
        "Review tier is selected by Tower according to the review's scope and reasoning needs",
        "independence or a two-pass format alone does not require the high-capability tier",
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
        "On the third independent failure with the same fingerprint under the same Work ID",
        "stop before a fourth low-tier attempt",
        "Failures with distinct fingerprints do not accumulate toward this threshold.",
        "a narrow, low-risk audit with clear acceptance criteria is appropriate for this tier",
        "independence or a two-pass checklist alone does not require a strong-model reviewer",
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
            "轻量工作默认交给 `tower-lightweight`",
            "调研、资料检索、事实核查、信息整理",
        ),
        (
            "新 Feature 按实际推理深度路由",
            "简单且范围明确的 Feature 交给 `tower-lightweight`",
            "确实需要深度设计的 Feature 才交给 `tower-high-capability`",
            "做详细 Spec/Plan",
            "再由轻量档 Build/Test/Fix/Retest",
        ),
        (
            "只有确实需要深度推理时才使用 `tower-high-capability`",
            "Build 默认交给 `tower-lightweight`",
        ),
        (
            "Build 默认交给 `tower-lightweight`",
            "普通 Build/Test/Fix/Retest 的首轮都交给轻量档",
            "同一 Work ID、同一失败指纹累计到第 3 次独立失败后",
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
            "首轮 Build 仍 route to `tower-lightweight`",
            "仅当 Build 确需深度推理时 route to `tower-high-capability`",
            "同一 Work ID 下同一失败指纹第 3 次独立失败",
            "高风险 verdict 不绕过轻量首轮",
            "否则交给 `tower-lightweight`",
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
            "先查遗漏、缺陷和回归",
            "再逐项追踪原始需求、验收标准、实现及测试/验证证据",
            "范围外想法记为 deferred",
        ),
        (
            "在开始 Build 前安排独立上下文的 Spec/Plan 评审",
            "按评审所需推理深度选择 Agent",
            "标准评审用 `tower-lightweight`",
        ),
        (
            "Build 完成后",
            "按核查所需推理深度选择 Agent",
            "只有确需深度推理时才用 `tower-high-capability`",
            "否则用 `tower-lightweight`",
            "独立核查仍执行两遍",
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
            "Reasoning Discipline",
            "precise, decision-relevant breadth and depth—not sheer volume",
            "Compare the useful angles against the request and available evidence",
            "Do not repeat unchanged reasoning",
            "otherwise synthesize and move on",
        ),
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
        source = (AGENT_SOURCE_DIR / f"{agent_id}.md").read_text()
        frontmatter = source.split("---", 2)
        if len(frontmatter) != 3:
            failures.append(f"{agent_id}: source frontmatter is missing or malformed")
        elif any(
            row.partition(":")[0].strip() == "model"
            for row in frontmatter[1].splitlines()
        ):
            failures.append(f"{agent_id}: model must not be pinned in source frontmatter")
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
