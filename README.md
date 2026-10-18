# MARIE Simulator

A Python MARIE execution engine with a retained Qt desktop application and a SvelteKit web playground. Write assembly, assemble, step or run, and inspect registers, all 4,096 memory words, and numeric input/output.

The web app uses **Python for all assembly and execution**. Svelte/TypeScript renders the editor and state; it does not simulate the machine. No database, paid service, or AI feature is required.

## Python package 1.2.0 (prepared, not yet published)

The PyPI distribution remains **marieSimulator**. The GitHub repository and web
app can use marie-simulator, but PyPI rejected that proposed distribution name as
too similar to an existing project. Existing installation and import names stay
compatible; no uninstall or package-name migration is needed.

This release packages the updated two-pass assembler and corrected MARIE engine.
The pure-Python engine has no required Qt or web dependencies. Python 3.10+ is
supported; Python 3.12 is tested. The optional desktop app requires PySide6.

After 1.2.0 is published, install the headless library with:

```sh
python -m pip install --upgrade 'marieSimulator==1.2.0'
```

For the retained desktop GUI, install the extra instead:

```sh
python -m pip install --upgrade 'marieSimulator[desktop]==1.2.0'
```

Assemble and run source directly, without Qt or the web service:

```python
from marieSimulator import Marie, assemble

program = assemble("Load X\nAdd X\nOutput\nHalt\nX, DEC 7")
machine = Marie(program, nonblocking=True)
machine.run()
assert machine.outputs == [14]
```

The wheel contains the Python engine, assembler, file reader and optional desktop
modules. The Svelte web app and its FastAPI backend remain separate checkout /
container applications; installing the wheel does not install or host the website.
See [release preparation](docs/releasing.md) and [changes](CHANGELOG.md).

## Run the web app locally

From this repository, in two terminals:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements-dev.txt
PYTHONPATH=src:backend .venv/bin/python -m uvicorn marie_api.app:app --host 127.0.0.1 --port 8000 --workers 1
```

```sh
cd web
bun install --frozen-lockfile
bun run dev
```

Open **http://127.0.0.1:5175**. Requires Python 3.12 and Bun 1.3.11. See [local/Docker/Coolify instructions](docs/deployment.md).

## Desktop and Python usage

```sh
.venv/bin/python -m pip install -r requirements.txt
PYTHONPATH=src .venv/bin/python main.py
```

```python
from marieSimulator import Marie, MarieReader
machine = Marie(MarieReader('trial'))
machine.run()
machine.show()
```

The retained GUI imports also work: `from marieSimulator import MarieGUI, app`. Headless engine imports do not initialize Qt.

```text
        Load    X
        Add     One
        Store   X
        Output
        Halt
X,      HEX     0000
One,    DEC     1
```

Supported instructions: JnS, Load, Store, Add, Subt, Input, Output, Halt, Skipcond, Jump, Clear, AddI, JumpI, LoadI, StoreI. Directives: HEX, DEC, ORG. Comments start with `/` or `;`. Addresses/HEX are hexadecimal; DEC is signed decimal. Values wrap to 16 bits. See [semantics and legacy fixes](docs/correctness.md).

## Tests and design

```sh
.venv/bin/python -m pytest -q
cd web
bun run check
bun run build
bunx playwright install chromium
bun run test:ui
```

Browser tests need the local servers running. Qt smoke tests skip if PySide6 is absent.

- [Architecture, session lifecycle, state machine, and limits](docs/architecture.md)
- [Correctness and compatibility notes](docs/correctness.md)
- [Deployment and configuration](docs/deployment.md)
- [Verification results and limitations](docs/verification.md)
- [Existing logo provenance](docs/branding.md)

Future work: breakpoints, sharing, import/export, lessons, and history. These are outside the initial release. Original Git history and historical distributions remain. Updated 1.2.0 distributions are prepared locally; publishing to PyPI and hosted deployment are separate actions.
