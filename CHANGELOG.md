# Changelog

Published release dates are the first PyPI upload date in UTC. Historical entries
were reconstructed from published wheels and Git history; they describe the
changes at that time, including import adjustments later revised again.

## Unreleased

- Remove tracked Python bytecode caches and macOS Finder metadata from the
  repository. Ignore rules keep these local files out of future commits.

## 1.2.1 — 2026-10-18 (UTC)

- Correct the package README after 1.2.0 was published: replace stale preparation
  status with normal install/upgrade instructions and a link to the live project.
- Documentation-only update; simulator and assembler code are unchanged.

## 1.2.0 — 2026-10-18 (UTC)

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

## 1.1.8 — 2023-04-18 (UTC)

- Initialize and pad simulator memory to 4,096 words.
- Add single-instruction execution through `step()`, reporting changed memory
  addresses, and disable further stepping after Halt.
- Encode and dispatch JnS with opcode 0; store assembled data words directly.
- Reject source files exceeding the reader's 4,096-line limit.
- Implement the desktop Step action, program-row and changed-memory highlighting,
  and clearing program highlights on reset. Display the full memory grid.
- Add a top-level desktop launcher.

## 1.1.7 — 2023-04-08 (UTC)

- Export both `MarieGUI` and the Qt `app` from the package root.
- Update desktop examples to import the GUI and application explicitly and use
  `app.exec()`; document the then-available macOS GUI download.

## 1.1.6 — 2023-04-08 (UTC)

- Remove the engine's direct `MarieReader` import and related type annotations.
- Reorder package initialization to import the GUI before the engine and reader.

## 1.1.5 — 2023-04-08 (UTC)

- Restore the GUI's relative engine and reader imports and the engine's reader
  import and type annotations.
- Export `MarieGUI` without `app` from the package root; empty the internal
  `main.py` launcher shim.

## 1.1.4 — 2023-04-08 (UTC)

- Restructure imports by removing the engine's direct reader dependency and
  related annotations, plus the GUI's relative engine and reader imports.

## 1.1.3 — 2023-04-08 (UTC)

- Replace the package's wildcard GUI export with explicit `MarieGUI` and `app`
  exports.

## 1.1.2 — 2023-04-08 (UTC)

- Expose GUI symbols through a wildcard import at the package root.
- Update the README desktop example to import from `marieSimulator`.

## 1.1.1 — 2023-04-08 (UTC)

- Introduce the Qt desktop interface with program, symbol, register and memory
  tables, plus Load, Reload, Run and Reset actions. Step remains a placeholder
  in this release.
- Add a GUI execution flag and hexadecimal console input/output outside GUI mode.
- List PySide6 in the repository requirements and replace duplicated simulator
  code in the internal launcher with GUI startup code.

## 1.1.0 — 2023-03-31 (UTC)

- Publish the earliest release still listed in current PyPI metadata, containing
  the file-based `Marie` simulator and `MarieReader` assembler.
- Normalize source-line whitespace to handle indentation and repeated spaces.
- Document a runnable assembly example with labels, Load/Add/Store/Halt and HEX
  data. The GUI module is still a placeholder.

## 1.0.1 — 2023-03-31 (repository milestone)

- Introduce Python packaging with a `src/marieSimulator` layout and package-level
  `Marie` and `MarieReader` imports.
- Add installation and example usage documentation.

This version is recorded in Git history. Current PyPI metadata does not list
release files for it, so publication has not been verified.

## Historical sources

- [PyPI release metadata](https://pypi.org/pypi/marieSimulator/json) provides
  published versions, artifact hashes and upload timestamps. Entries for
  1.1.0–1.1.8 were checked against the Python sources in those published wheels.
- [Repository history](https://github.com/dehadeaaryan/marie-simulator/commits/main/)
  provides packaging and documentation context. Versions 1.1.3–1.1.6 have no
  separate release commits; their entries come from successive wheel comparisons.
- Historical behavior can differ from the corrected 1.2.0 engine; see
  [the correctness reference](docs/correctness.md) for current semantics.
