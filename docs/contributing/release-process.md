# Release Process

This project uses semantic versioning once the public API reaches 1.0. Before 1.0, avoid breaking
the stable CLI flags, output filenames, output column names, QC flag names, and public function
signatures unless the changelog calls it out clearly.

## Maintainer Checklist

1. Decide the version number.
2. Update `CHANGELOG.md`, moving entries from `[Unreleased]` into `## [X.Y.Z] - YYYY-MM-DD`.
3. Bump `version` in `pyproject.toml`.
4. Confirm `src/meaorganoid/__init__.py` resolves the installed package version.
5. Run `scripts/dev/check_repo_health.sh`.
6. Commit the release prep.
7. Create and push the tag:

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

8. Verify the GitHub Release contains the sdist and wheel artifacts.
9. Verify PyPI publication completed through trusted publishing.
10. Confirm Zenodo minted a DOI for the GitHub Release.
11. Update `CITATION.cff` with the real Zenodo DOI. Add manuscript references under
    `references:` once a bioRxiv or journal link exists.

## PyPI Trusted Publishing

The release workflow uses `pypa/gh-action-pypi-publish` with GitHub OIDC. No password secret should
be added. A PyPI project owner must configure a trusted publisher for this repository, workflow
file, and environment if one is later introduced.

See:

- <https://docs.pypi.org/trusted-publishers/>
- <https://github.com/pypa/gh-action-pypi-publish>

## Zenodo

Enable the GitHub-Zenodo integration for the repository before the first release. After pushing a
`vX.Y.Z` tag, Zenodo should archive the GitHub Release and mint a DOI. Replace the placeholder DOI
in `CITATION.cff` with the concept DOI or version DOI chosen for citation.
