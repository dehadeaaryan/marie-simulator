# MARIE Simulator

A Python MARIE execution engine with a retained Qt desktop application and a SvelteKit web playground. Write assembly, assemble, step or run, and inspect registers, all 4,096 memory words, and numeric input/output.

The web app uses **Python for all assembly and execution**. Svelte/TypeScript renders the editor and state; it does not simulate the machine. No database, paid service, or AI feature is required.

## Install the Python package

The distribution is [marieSimulator](https://pypi.org/project/marieSimulator/).
Install or upgrade the headless library with:

```sh
python -m pip install --upgrade marieSimulator
```

The pure-Python engine has no required Qt or web dependencies. Python 3.10+ is
supported; Python 3.12 is tested. The package includes the shared two-pass
assembler and MARIE execution engine.

For the retained desktop GUI, install the extra instead:

```sh
python -m pip install --upgrade 'marieSimulator[desktop]'
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

Future work: breakpoints, sharing, import/export, lessons, and history. These are outside the initial release. Original Git history and historical distributions remain. The Python package is published on PyPI; website hosting remains a separate deployment.
