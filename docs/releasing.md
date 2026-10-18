# Python package releases

Prepared version: **1.2.0**, following 1.1.8 on the existing **marieSimulator**
PyPI project. Python imports remain marieSimulator. Keeping the existing project
preserves release history and normal upgrades. The proposed marie-simulator
project name was rejected by PyPI as too similar; it is not used by this release.
The GitHub repository can retain its marie-simulator name independently.

## Validate and build

The Python 3.12 checkout passes all 68 tests, including the optional offscreen Qt
desktop smoke test. Headless imports have no Qt or web dependencies.

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider
python -m pip install --upgrade build twine
python -m build
python -m twine check --strict dist/mariesimulator-1.2.0-py3-none-any.whl dist/mariesimulator-1.2.0.tar.gz
```

Current preparation builds from a temporary clean source tree to preserve the
historical tracked 1.1.8 distributions and egg-info. Current setuptools lowercases
the distribution in filenames; the wheel's metadata name remains marieSimulator.
The wheel contains the updated engine, assembler, reader and optional desktop
modules. The web frontend and FastAPI backend are separate applications.

Inspect archives for credentials, .env, .DS_Store, caches, databases and generated
files; exclude web/backend services and nested distribution archives. Rebuild a
wheel from the source archive and test an installed wheel outside the checkout,
both without Qt and with the optional desktop dependency. The release preparation
performs those checks, plus Twine's strict metadata check.

## Publish explicitly

Run from the repository root after reviewing and committing source:

```sh
.venv/bin/python -m twine upload --repository pypi dist/mariesimulator-1.2.0-py3-none-any.whl dist/mariesimulator-1.2.0.tar.gz
```

Use your PyPI API token at Twine's hidden prompt. Never include it in source,
command arguments or chat. Use the exact files above, not dist/*: historical
releases and superseded names must not be uploaded. Superseded unpublished
marie-simulator 1.2.0 files were moved out of dist/ during final preparation.
Building and checking do not publish anything. If 1.2.0 has already been published,
choose a new version rather than attempting to overwrite immutable PyPI files.

## Install after publication

Existing users can upgrade normally; no package uninstall or import rename is
needed:

```sh
python -m pip install --upgrade 'marieSimulator==1.2.0'
# Optional retained desktop GUI:
python -m pip install --upgrade 'marieSimulator[desktop]==1.2.0'
```

Python 3.10+ is supported; local tests run on 3.12. The desktop extra requires
PySide6 6.11.0. Neither the website nor its API/analytics services are installed or
started by a Python library import.

## PyPI name restriction

An absent public project page does not prove registration eligibility. PyPI
rejected marie-simulator with HTTP 400 because it is too similar to an existing
name. A different Twine command or --skip-existing cannot resolve that restriction.
This release therefore retains marieSimulator by the maintainer's choice. The
existing PyPI project must not be deleted for this migration.

Reference: https://pypi.org/help/#project-name
