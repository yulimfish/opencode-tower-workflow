# Tower 多 Agent 协作与进度管理工作报告

日期：2026-10-10
状态：配置与规则落地完成；模型绑定后的真实委派验证待完成。

## 执行摘要

本项工作建立并完善了 Tower 多 Agent 协作约定：由总控负责拆解需求、评估难度与风险、提取范围和验收标准并统一管理进度；高能力与轻量 Agent 表示模型能力档位，不是固定 Planner/Builder 职位。新增“显性监督失败”升档规则，避免轻量模型在同一问题上重复失败造成时间和资源浪费。

## 实施内容

### 1. Tower Agent 基础路由

- `tower-controller` 作为唯一总控，负责需求拆解、难度/风险路由、上下文交接、进度汇总和完成证据核验；不直接实现代码。
- `tower-high-capability` 默认承担新 Feature 的头脑风暴、Spec、Plan 和高难任务分析；`tower-lightweight` 默认承担规划后的 Build/Test/Fix/Retest。
- 简单、清楚、低风险的非 Feature 任务允许轻量 Agent 独立端到端完成。高能力档位不被限制为“只做计划”，可在明确升档时接手实现。
- 模型型号不写入 Agent 定义；由用户在 OpenChamber 绑定。

### 2. 统一进度台账与交接

- 每个可独立委派的工作项分配唯一 Work ID，并记录负责人、状态、依赖、验收标准/交付物、验证证据和下一步。
- 状态统一为 `queued`、`in_progress`、`blocked`、`done`；没有交付物和验证证据不得标为 `done`。
- 派发前登记，派发、回报、阻塞、重分配、返工或完成时更新台账；仅并行处理互不依赖的工作项。
- 子 Agent 在进度与最终回报中回显 Work ID 和状态；交接携带完成任务所需的范围、验收、依赖、文件/产物及验证信息。
- 进度按里程碑简明汇报；上下文压缩时保留当前台账、未完成项、依赖、证据和下一步，不默认另建重复的进度文档。

### 3. “显性监督失败”升档

- Controller 按 Work ID 记录失败指纹、独立尝试次数、已尝试修正及验证证据。根因尚未定位时，以失败测试/命令和稳定错误现象作为指纹。
- 一次独立尝试指一轮实质性实现/修正及其对应验证；同一轮里重复出现的日志或报错只计一次。
- 同一 Work ID、同一失败指纹第 3 次失败，立即标记“显性监督失败”，停止轻量 Agent 重复同一修正路线，并将负责人升级为 `tower-high-capability`。
- 高能力 Agent 接手根因分析和 Build/Fix/Retest，而不是只返回另一份 Plan。若高能力档位不可用，则停止重试并将工作项标为 `blocked`。
- 该规则是默认路由的例外：通常高能力做 Plan、轻量做 Build；出现同问题三次失败时由高能力接管 Build。

## 验证与复核

- 扩展配置 smoke test，检查三个 Agent 的运行时发现、模式、路由/交接标记、进度台账规则、失败升档规则及总控权限。
- 测试先按预期失败，补齐配置后从根目录 `/` 执行通过。测试命令：

  ```bash
  python3 tests/2026-10-09-tower-agent-config-smoke-test.py
  ```

- 曾发现测试器继承调用者工作目录会导致 OpenCode 找不到全局 Agent；现已固定用测试脚本所在目录启动发现命令，从 `/` 运行也通过。
- 独立复核未发现 BLOCKER 或 MAJOR。复核为 CONDITIONAL PASS 的唯一限制是模型尚未绑定，因此 smoke test 只能证明配置加载和提示词契约，不能证明模型真实执行失败计数、升档和跨 Agent 接管。

## 交付物

- Agent 配置：`agents/tower-controller.md`、`agents/tower-high-capability.md`、`agents/tower-lightweight.md`
- 配置验证：`tests/2026-10-09-tower-agent-config-smoke-test.py`
- 工作流设计及 Loop 看板复用规则：`docs/tower/2026-10-09-tower-agent-workflow-design.md`（含 2026-10-10 补充）

## 后续建议

在 OpenChamber 绑定两档模型后，执行一次受控委派，验证轻量 Agent 对同一失败指纹的独立尝试计数，以及第 3 次失败后高能力 Agent 是否实际接管 Build/Fix/Retest。未来实现 Loop 看板时，沿用本报告中的工作项字段、四态状态机，并把升档原因/失败次数作为独立事件信息，而不是新增第五种状态。
