# Support and compatibility

Alpha software with community support and no managed-service SLA. Questions and
bugs go to GitHub issues on this repository; `support@liquidlm.com` is the
fallback channel. Hosted service access is separate from the source license.
Operation availability follows the server's public API contract and the
caller's scopes.

Supported runtime: Python 3.11–3.14. Verified for this release: mocked
transport tests, lint, strict typing, examples and wheel/sdist content checks
on Python 3.14.6 and the 3.11.14 floor (macOS ARM64), plus clean-venv wheel
install. The hosted CI matrix (3.11–3.14 on Ubuntu and macOS) runs on every
push to this repository.

Use semver for API-affecting changes; document credential or configuration
migrations explicitly. Browser/JavaScript usage is out of scope for this SDK;
use the TypeScript client there.

## Release policy

Same policy as the TypeScript clients: semver for API-affecting changes,
prerelease line support (newest alpha gets fixes), explicit deprecation
warnings for at least one minor line, and immutable published versions with
deprecate-and-supersede rollback. Contract snapshots pin across the
TypeScript/Python pair — a contract change releases both together.
