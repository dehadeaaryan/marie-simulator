# MARIE behavior and legacy findings

The implementation was inspected directly, not inferred from the README. All 15 instruction dispatches existed: JnS, Load, Store, Add, Subt, Input, Output, Halt, Skipcond, Jump, Clear, AddI, JumpI, LoadI, StoreI. The desktop's edit/save menu actions were placeholders. This work retains those legacy placeholders; the web editor is independent.

## Defined semantics

- Memory has exactly 4,096 unsigned 16-bit stored words. AC, MBR, IR, input and output represent raw 16-bit words; signed display interprets bit 15 as two's-complement sign. Arithmetic wraps modulo 65,536. PC and MAR are 12-bit addresses.
- Instructions encode a 4-bit opcode in bits 15–12 and an address/condition in bits 11–0. F is not an executable instruction. Data has no protected type; a data word whose high nibble is a valid opcode can execute if control flows into it, just like MARIE memory.
- PC increments before execute and wraps from FFF to 000. Branches use 12-bit addresses. Indirect instructions read a pointer at X, then use its low 12 bits; high pointer bits are ignored intentionally.
- Skipcond 000 checks signed AC < 0; 400 checks zero; 800 checks signed AC > 0. The assembler rejects every other condition. Runtime C00 is undefined and produces an execution error, including for self-modified code.
- JnS stores the already incremented PC at X and sets AC and PC to X+1. It **clobbers AC** by design. A subroutine must save the caller's accumulator before JnS when needed. JumpI returns through the saved address.
- Numeric addresses, ORG, and HEX operands are hexadecimal. DEC operands are decimal and must be −32768…32767. HEX accepts raw 0000…FFFF or signed −8000…−1. Labels are case-insensitive and must precede a comma. Forward labels are resolved in a second pass. Blank lines and `/` or `;` comments do not allocate memory. ORG sets the next address; overlapping ranges fail. The first allocated word determines entry PC.
- Input/output use a complete numeric 16-bit word. This educational app intentionally supports 16-bit numeric I/O instead of an 8-bit character-oriented MARIE variant. There is no ASCII mode initially.

## Bugs found and corrected

| Existing behavior | Correction and compatibility impact |
| --- | --- |
| Package import created QApplication and required PySide6 | Lazy desktop imports; `from marieSimulator import MarieGUI, app` still works |
| `Marie.parse` reused and extended the reader's memory | Copy and pad the program; mutations and resets cannot corrupt the initial image |
| Indirect operations skipped fetching M[X], so MBR still held the instruction | Fetch pointer words for AddI, JumpI, LoadI, StoreI; mask indirect addresses |
| Python integers could overflow the word width; HEX FFFF appeared positive to Skipcond | Normalize words and evaluate signed AC for conditions |
| PC could leave memory bounds | 12-bit PC wrapping |
| Opcode F silently did nothing | Fail execution clearly |
| GUI Input used a busy-wait; Run could block the UI | Nonblocking input for API, Qt input dialog for desktop; desktop Run uses a timer |
| File assembler could crash on blanks, reinterpret data as instructions, or encode unresolved labels as −1 | Shared two-pass assembler with explicit errors and source lines |
| Store highlighting passed a float row index to Qt | Integer row division and guarded table access |
| Canceled file load tried opening an empty filename | Preserve the current desktop program on cancellation/error |

The assembler intentionally tightens acceptance: unknown instructions no longer act as HEX, unresolved labels and extra/missing operands fail, duplicate labels fail, and only valid Skipcond operands are allowed. Existing valid `trial` syntax and the desktop/CLI interfaces remain supported. Blank/comment handling, DEC, and ORG are added. Python 3.10+ is now required; Python 3.12 is used and tested for the API and containers. Old distributable files remain untouched historical artifacts; no package release has been built or published.

## Verification

Engine tests cover all encodings, forward labels, source lines, overflow/underflow, signed Skipcond truth tables, indirect read/add/write, pointer high bits, JnS/JumpI, origin/PC wrapping, input yields, halted stepping, invalid execution, malformed programs, source byte limits, and copy-based reset.

API tests cover assembly diagnostics, stepping/running/input/reset, responsive Pause, concurrent stale commands, owner isolation for reads/mutations/deletion/replacement, expiry/cleanup, restart loss, capacities, instruction/output/time limits, input validation, request size, and cross-origin rejection. Limits are lowered in tests to exercise boundaries quickly rather than making tests spend the full production budget.

Optional Qt smoke testing loads a file, steps, runs via timer, outputs, resets memory, and supplies input without interactive dialogs. Browser tests cover the full editing/assembly/run path, memory inspection, input, examples, source/session/theme persistence, diagnostic highlighting, network/expiry states, responsive controls, and WCAG A/AA checks on desktop/mobile viewports. See `docs/verification.md` for this workspace's actual results and remaining checks.
