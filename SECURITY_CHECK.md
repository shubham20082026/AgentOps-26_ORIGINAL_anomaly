# Credential and Git history check

## Verified scope

A scan of all blobs reachable from local Git refs (including fetched public main) compares bytes against the current configured API key and recognizable Google API key, provider key, GitHub token and private-key patterns. Text/XML entries within ZIP-based files such as PowerPoint are also inspected. The prepared working tree is checked separately. Secret values are never printed in the report.

- `.private/api.dpapi`, `.env`, `.env.production` and `.streamlit/secrets.toml` match `.gitignore`.
- No files under `.private`, `.env*` or `.streamlit/secrets.toml` are tracked.
- No matching credential or current API key was detected in the scanned reachable history.
- No matching credential or current API key was detected in the checked publishable working files.

This is a scoped detection result, not a proof about every possible secret format. It does not certify unreachable local objects, remote-only deleted refs, caches, old forks, screenshots or provider-side logs. If a key is ever published, revoke/rotate it; adding an ignore rule does not remove prior exposure. No history rewrite was needed for this scan result.

## Recheck before publishing

```text
git check-ignore .private/api.dpapi .env .env.production .streamlit/secrets.toml
git ls-files .private .env '.env.*' .streamlit/secrets.toml
```

The first command should list every example path; the second should produce no output. Use a maintained secret scanner as an additional check in the authenticated release workflow. Store hosted credentials in Streamlit Secrets; the Windows-encrypted key remains local. Do not include a real key in issue reports or screenshots.
