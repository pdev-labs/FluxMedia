# FluxMedia Agent Rules

## Automated Releases, Versioning and Changelogs
Whenever you modify code and push it to the GitHub repository, you MUST:
1. Update `CHANGELOG.md` with a summary of your changes under a new version heading. If `CHANGELOG.md` does not exist, create it.
2. Update the "Latest Release" section in `README.md` to reflect the new version and its highlights.
3. Increment the version number in `pyproject.toml` (e.g. from `1.6.13` to `1.6.14`).
3. Commit and push the changes.
4. Automatically create a GitHub release for the new version using the GitHub CLI:
   ```bash
   gh release create v1.x.x --generate-notes
   ```
   Do not ask for permission to do this if the user has requested a fix or feature that you are deploying.
