# Versioning and change log

## Project version

The single source of truth is the [`VERSION`](../VERSION) file (SemVer `MAJOR.MINOR.PATCH`).

| Bump | When |
|------|------|
| MAJOR | Breaking BSP API change, or a new board hardware revision that is not backward compatible |
| MINOR | New board, new BSP feature/driver, new test, new schematic sheet |
| PATCH | Bug fixes, doc corrections, small schematic fixes |

While the version is `0.x`, the API is not yet considered stable.

## Workflow for every change

1. Make the change.
2. Add an entry under `## [Unreleased]` in [`CHANGELOG.md`](../CHANGELOG.md)
   (sections: Added / Changed / Fixed / Removed).
3. Commit with a clear message.

## Making a release

1. Decide the new version and write it to `VERSION`.
2. In `CHANGELOG.md`, rename `[Unreleased]` to `[x.y.z] - YYYY-MM-DD`, add a new
   empty `[Unreleased]` section, and update the compare links at the bottom.
3. Commit: `Release vX.Y.Z`
4. Tag and push:
   ```sh
   git tag -a vX.Y.Z -m "Release vX.Y.Z"
   git push origin main --tags
   ```

## Hardware revisions

KiCad projects carry their own board revision (e.g. `Rev A`, `Rev B`) in the
schematic title block. Record each hardware revision change in `CHANGELOG.md`
and in the board's `README.md`.
