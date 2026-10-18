# Changelog

## 1.2.0 — unreleased

Publication under marie-simulator is blocked by PyPI's similar-name restriction.

- Rename the PyPI distribution to marie-simulator while retaining marieSimulator
  imports. The new project has separate history and requires explicit migration.

- Package the shared two-pass assembler with source locations, forward labels,
  blank/comment handling, DEC/HEX/ORG directives and explicit assembly errors.
- Correct 16-bit arithmetic, signed Skipcond, indirect addressing, JnS/JumpI,
  invalid-instruction handling and 12-bit address wrapping.
- Copy program memory so execution/reset cannot mutate the original program.
- Add nonblocking input and output queues for headless embedding.
- Keep Qt optional through lazy desktop imports and the desktop dependency extra.
- Retain Marie, MarieReader and desktop import compatibility. Valid legacy trial
  programs remain supported; malformed assembly is now rejected explicitly.
- Package source documentation and engine/desktop tests, excluding web/backend,
  credentials and generated artifacts from source archives.

The separate web simulator uses the same Python engine, but web/frontend/backend
services are not included in the Python wheel. See docs/correctness.md for exact
semantics, changes from legacy behavior, and intentional limitations.
