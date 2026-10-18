# MARIE Simulator

A Python MARIE execution engine with a retained Qt desktop application and a SvelteKit web playground. Write assembly, assemble, step or run, and inspect registers, all 4,096 memory words, and numeric input/output.

The web app uses **Python for all assembly and execution**. Svelte/TypeScript renders the editor and state; it does not simulate the machine. No database, paid service, or AI feature is required.

## Python package 1.2.0 (prepared, not yet published)

**Publication is currently blocked:** PyPI rejected `marie-simulator` as too similar
to an existing project. A 404 project-page check does not establish that PyPI will
accept a name. The install commands below apply only after a successful publish.
Keeping this name requires resolving the restriction with PyPI; otherwise rebuild
under the existing `marieSimulator` distribution or an accepted alternative name.

This release packages the updated two-pass assembler and corrected MARIE engine.
The pure-Python engine has no required Qt or web dependencies. Python 3.10+ is
supported; Python 3.12 is tested. The optional desktop app requires PySide6.

After 1.2.0 is published, install the headless library with:

```sh
python -m pip install --upgrade 'marie-simulator==1.2.0'
```

For the retained desktop GUI, install the extra instead:

```sh
python -m pip install --upgrade 'marie-simulator[desktop]==1.2.0'
```

### Migrating from the old PyPI name

The distribution is now **marie-simulator**. Python imports remain
`marieSimulator`, so existing source code keeps working. This is a new PyPI
project, not an automatic rename of the old project: previous release history,
download totals and automatic upgrades do not transfer.

In an existing environment, remove the old distribution before installing the
new one, because both distributions provide the same Python import directory:

```sh
python -m pip uninstall marieSimulator
python -m pip install 'marie-simulator==1.2.0'
```

Desktop users should install `marie-simulator[desktop]==1.2.0` instead. Also update
requirements and lockfiles that reference the old distribution name. Fresh
virtual environments need only the new install command. Do not install both
names together. The old `marieSimulator` project remains separate and unchanged.

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
