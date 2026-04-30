# Codex Task 11 — CI + release prep

## Workflow context

Touches no workflow's logic; sets up CI, coverage, and the path to a citable v0.1.0 release. After this task, every PR must pass CI before merging, and the project is ready for a tagged release with a Zenodo DOI.

## Pre-task

1. Read `AGENTS.md` § "Definition of done". CI must enforce these rules mechanically.
2. Read existing GitHub Actions workflow files. The README references `ci.yml` but the file may not yet exist.
3. Run `pytest -q --cov=meaorganoid --cov-report=term-missing` locally and note the current coverage percentage.

## What to do

1. Create `.github/workflows/ci.yml`. Triggers: `push` and `pull_request` on any branch. Jobs:

   * **lint** (ubuntu-latest, Python 3.11): runs `ruff check`, `ruff format --check`, `mypy --strict src/`.
   * **test** (matrix over ubuntu-latest + macos-latest, Python 3.10/3.11/3.12): runs `pytest -q --cov=meaorganoid --cov-report=xml`, then uploads `coverage.xml` as an artifact and to Codecov via `codecov/codecov-action@v4`. Fails the job if coverage drops below `--cov-fail-under=80`.
   * **doctests** (ubuntu-latest, Python 3.11): runs `pytest --doctest-modules src/`.
   * **integration** (ubuntu-latest, Python 3.11): runs `pytest -q -m integration` separately so a slow integration test failure is visible without blocking unit feedback.
   * **build** (ubuntu-latest, Python 3.11): runs `python -m build` and uploads the `dist/*` as an artifact. Verifies the wheel is installable in a fresh venv.

   All jobs install with `pip install -e ".[dev]"`. Use `actions/setup-python@v5` with pip caching keyed on `pyproject.toml`.

2. Create `.github/workflows/release.yml`. Triggered by pushing a tag matching `v*.*.*`:

   * Build sdist and wheel.
   * Generate release notes from the matching `CHANGELOG.md` section.
   * Create a GitHub Release with the artifacts attached.
   * Publish to PyPI via OIDC trusted publishing (do **not** add a password secret). Document the trusted-publisher setup in `docs/contributing/release-process.md` so a maintainer can wire the PyPI side once.

3. Create `.github/workflows/docs.yml` (or extend the one from Task 10) to also run on PRs and post a sticky comment with the build outcome.

4. Add a `pre-commit` config at `.pre-commit-config.yaml` running:
   * `ruff check --fix`
   * `ruff format`
   * `mypy --strict src/` (only on push, not commit, since it is slow)
   * `mkdocs build --strict` (only on docs/* changes, via `files:` filter)

5. Update `pyproject.toml`:
   * Add `coverage[toml]` to the `dev` extra.
   * Add a `[tool.coverage.run]` section with `branch = true` and `source = ["src/meaorganoid"]`.
   * Add a `[tool.coverage.report]` section with `fail_under = 80` and `exclude_also = ["if TYPE_CHECKING:", "raise NotImplementedError"]`.

6. Verify repository URLs in `pyproject.toml` and `README.md` point to `zdx8910/axion-organoid-pipeline`.

7. `CHANGELOG.md`: cut the `[Unreleased]` section into `## [0.1.0] - <today>` with the workflow A–H feature list, error-class additions, CLI surface, and CI bring-up. Keep a fresh empty `[Unreleased]` heading above it.

8. `CITATION.cff`: replace the preprint placeholder with a Zenodo concept-DOI placeholder (`10.5281/zenodo.PLACEHOLDER`) and add a comment explaining where to update it after the first GitHub Release tag triggers Zenodo to mint a DOI. Add the manuscript reference to `references:` once the bioRxiv link exists.

9. Add `docs/contributing/release-process.md` documenting the full release flow:
   * Decide version (semver — public API freeze rules from AGENTS.md).
   * Update `CHANGELOG.md`.
   * Bump version in `pyproject.toml` and `src/meaorganoid/__init__.py`.
   * Tag `vX.Y.Z` and push.
   * Verify GitHub Release artifacts.
   * Verify PyPI publication.
   * Confirm Zenodo DOI minted; update `CITATION.cff`.

10. Add a status-badge row to `README.md`:
    * CI status
    * Codecov coverage
    * PyPI version
    * Python versions
    * License
    * DOI (placeholder until first release)

## Tests to add

* No new pytest tests required.
* Add a `scripts/dev/check_repo_health.sh` that runs the same commands the CI runs, in order, against the local checkout. PR description must show its output.

## Success criteria

* `act -j lint` (or local equivalent — at minimum running each step manually) passes for every CI job.
* Coverage report ≥ 80% on `main`. If under, add tests in this PR until it isn't, **without** lowering the threshold.
* `pre-commit run --all-files` passes.
* CHANGELOG `[0.1.0]` section accurately reflects the merged feature set from tasks 01–10.
* `CITATION.cff` validates with `cffconvert --validate`.

## What NOT to do

* Do **not** add a password-based PyPI deploy. Trusted publishing only.
* Do **not** lower the coverage threshold to make CI green. Add tests instead.
* Do **not** remove any AGENTS.md rule that CI now enforces. CI is the enforcement, AGENTS.md is the contract.
* Do **not** silently extend AGENTS.md without surfacing the change in the PR description.

## Deliverable

PR titled `chore: ci + release pipeline + v0.1.0 cut` with:

* A summary of the five CI jobs and what each enforces.
* Coverage percentage achieved on `main` after this PR.
* The `[0.1.0]` `CHANGELOG.md` section as inline preview.
* The output tail of `pre-commit run --all-files`.
* A note on the Zenodo / PyPI trusted-publisher setup the maintainer still has to complete out-of-band, with links to the GitHub docs.
