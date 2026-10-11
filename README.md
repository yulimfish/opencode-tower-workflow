# opencode-tower-workflow

OpenCode Tower 工作流套件，包含一个控制器和两个按模型能力分层的 Agent。这些 Agent 不绑定特定模型；请在 OpenChamber 中为它们配置所需模型。

## 内容

- `agents/tower-controller.md` — 负责协调任务范围、路由、进度跟踪和审查。
- `agents/tower-high-capability.md` — 负责功能探索、Spec/Plan 编写、审查以及升级处理的实现任务。
- `agents/tower-lightweight.md` — 负责范围明确的实现与验证。
- `docs/` — 按日期归档的工作流设计、Spec、Plan 和运行记录。
- `tests/2026-10-09-tower-agent-config-smoke-test.py` — 检查 Agent 发现、提示词契约、任务路由和权限配置。

此冒烟测试会检查 OpenCode 的 Agent 发现和配置；它不会运行模型，也不能证明基于模型的委派功能正常。请使用隔离的临时配置运行，以免修改现有 Agent：

```bash
test_config="$(mktemp -d)"
mkdir -p "$test_config/agents"
cp agents/*.md "$test_config/agents/"
OPENCODE_CONFIG_DIR="$test_config" python3 tests/2026-10-09-tower-agent-config-smoke-test.py
```

如需通过 workflow kit 安装，请运行其安装程序；也可以克隆本仓库，并将 `agents/*.md` 复制到 `~/.config/opencode/agents/`。

## 许可证

MIT。详见 `LICENSE`。
