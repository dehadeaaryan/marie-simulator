# Python package releases

Prepared version: **1.2.0**, under the new PyPI distribution **marie-simulator**.
The old marieSimulator distribution remains at its previous release; Python
imports stay marieSimulator for source compatibility. Only Python library/desktop modules ship in the wheel; the web
frontend and FastAPI backend are separate applications.

## Validate and build

Run Python tests from the checkout with its Python 3.12 environment:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider
```

For normal release preparation, install packaging tools in a dedicated environment
and build the source archive and wheel:

```sh
python -m pip install --upgrade build twine
python -m build
python -m twine check --strict dist/marie_simulator-1.2.0-py3-none-any.whl dist/marie_simulator-1.2.0.tar.gz
```

The current preparation builds from a temporary clean source copy, preserving
historical tracked 1.1.8 archives and egg-info rather than overwriting them.
The output filenames normalize the distribution hyphen to an underscore by current setuptools.

Inspect archive contents: include Marie.py, MarieReader.py, assembler.py,
MarieGUI.py and __init__.py; exclude .env, credentials, .DS_Store, caches, virtual
environments, web/backend services and nested distribution archives. The source
archive should include correctness notes, release docs and the offline engine /
desktop tests. Rebuild a wheel from the source archive as a completeness check.
Test imports and a small program from the installed wheel outside the checkout,
including an environment without Qt. Desktop smoke tests use QT_QPA_PLATFORM=offscreen.

## Publishing blocker

PyPI rejected the new project with HTTP 400: "The name 'marie-simulator' is too
similar to an existing project." The earlier HTTP 404 only showed that the public
project endpoint was absent; it did not prove registration eligibility.

This is a registry name restriction, not a Twine syntax, wheel validation or token
error. Retrying with --verbose, upgrading Twine, changing filename punctuation or
using --skip-existing does not resolve it. Do not delete the old project to try
to work around the restriction.

Keep the rename pending a request to PyPI support, or explicitly choose another
distribution name (including retaining marieSimulator) and rebuild. The upload
command below can succeed under this name only after PyPI permits it.

Reference: https://pypi.org/help/#project-name

## Publish explicitly

After reviewing and committing the source, publish only these versioned files:

```sh
python -m twine upload --repository pypi dist/marie_simulator-1.2.0-py3-none-any.whl dist/marie_simulator-1.2.0.tar.gz
```

Use a PyPI API token through Twine's hidden prompt or supported credential store.
Do not put it in source or command arguments. Building and checking do not upload
anything. PyPI releases are immutable: if 1.2.0 already exists, choose a new version.

## Compatibility

Python 3.10+ remains the package minimum; the local suite is run on 3.12. The
headless engine requires no external runtime dependencies. Desktop users install
marie-simulator[desktop], which requires PySide6 6.11.0. No website, API, database or
analytics service is installed or started by a library import.

## Migration and first publication

The new project name is marie-simulator. The old name normalizes to
mariesimulator, which is a different project. The new name was checked and
returned HTTP 404 before preparation; this does not reserve it. A successful first upload creates the new project only if PyPI permits the name.
The attempted upload has now demonstrated that this name is blocked.

Use exact new artifact names, never dist/*, because dist/ also contains historical
1.1.8 releases under the old name. The superseded, unpublished 1.2.0 artifacts
under the old name have been moved out of dist/ during rename preparation.

Users with the old distribution installed should uninstall marieSimulator and
then install marie-simulator (or its desktop extra). Both names provide the same
marieSimulator import directory and must not be installed together. Existing
Python import statements need no edits. Historical download totals and releases
do not migrate, and existing users do not automatically upgrade to the new name.
