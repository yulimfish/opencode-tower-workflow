# opencode-tower-workflow

An OpenCode Tower workflow bundle with a controller and two model-capability-tier agents. The agents are model-agnostic; bind the desired models in OpenChamber.

## Contents

- `agents/tower-controller.md` — coordinates scope, routing, work tracking, and reviews.
- `agents/tower-high-capability.md` — handles feature discovery, Specs/Plans, reviews, and escalated implementation.
- `agents/tower-lightweight.md` — handles bounded implementation and verification.
- `docs/` — dated workflow design, Specs, Plans, and operating records.
- `tests/2026-10-09-tower-agent-config-smoke-test.py` — checks agent discovery, prompt contracts, routing, and permissions.

The smoke test checks OpenCode agent discovery and configuration; it does not run models or prove model-backed delegation. Run it against an isolated temporary config so existing agents are not changed:

```bash
test_config="$(mktemp -d)"
mkdir -p "$test_config/agents"
cp agents/*.md "$test_config/agents/"
OPENCODE_CONFIG_DIR="$test_config" python3 tests/2026-10-09-tower-agent-config-smoke-test.py
```

To install with the workflow kit, run its installer or clone this repository and copy `agents/*.md` into `~/.config/opencode/agents/`.

## License

MIT. See `LICENSE`.
