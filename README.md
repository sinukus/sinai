# AI Court

AI Court is a small Python framework for running the same prompt through multiple AI backends, then using a separate judge to compare the answers and select a winner.

The core design goals are:

- backend-agnostic interfaces
- explicit cost tracking
- deterministic, testable orchestration
- pluggable memory/context
- a clean path toward Android and other clients

See `docs/ARCHITECTURE.md` and `docs/ROADMAP.md` for the current design and next steps.

## Local travel app

A runnable local text UI is available. See [travel setup](docs/TRAVEL.md) for installation, local model configuration, streaming behavior and remaining native-mobile limitations.
