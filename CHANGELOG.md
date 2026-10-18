# Changelog

## 1.2.0 — unreleased

The distribution remains marieSimulator; normal upgrades and imports stay compatible.

- Retain the existing marieSimulator PyPI project after PyPI rejected the proposed
  marie-simulator name. Existing users need no package-name migration.

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
