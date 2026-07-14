# FluxMedia Agent Rules

## Automated Releases and Versioning
Whenever you modify code and push it to the GitHub repository, you MUST:
1. Increment the version number in `pyproject.toml` (e.g. from `1.6.13` to `1.6.14`).
2. Commit and push the changes.
3. Automatically create a GitHub release for the new version using the GitHub CLI:
   ```bash
   gh release create v1.x.x --generate-notes
   ```
   Do not ask for permission to do this if the user has requested a fix or feature that you are deploying.
