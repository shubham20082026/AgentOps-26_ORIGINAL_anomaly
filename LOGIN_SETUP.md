# Dispatcher login

Run `python configure-login.py` locally and enter a unique password at the hidden prompts. It prints a salted PBKDF2-SHA256 hash with 600,000 iterations. It does not save the password. Keep the hash private too.

In Streamlit Cloud, open Manage app, Settings, Secrets. Keep your existing API settings and add:

```toml
REROUTE_REQUIRE_LOGIN = true
REROUTE_LOGIN_USER = "your-dispatcher-name"
REROUTE_LOGIN_HASH = "paste-the-generated-hash-here"
```

Save and reboot the app. Test sign-in and sign-out in a private browser. Never put passwords or real hashes in GitHub. Environment variables with the same names work locally. Any partial login configuration blocks access until corrected. With no login settings, the app stays an explicitly labeled public synthetic sandbox and the sidebar sign-in button opens setup guidance. There are no default credentials or registration.

Configured login gates the workspace, data, evaluation and provider calls before opening the database. Approvals use the signed-in account name. Sessions expire after one hour, reloads may require a new login, credential changes invalidate existing sessions, and sign-out clears session state. Five attempts per process per minute are allowed, shared across users. This can briefly block legitimate users and does not replace an identity provider or distributed rate limiting.

This is one dispatcher account, not role-based access, tenant isolation, multi-user account management or independent reviewer authorization. Local SQLite and audit protection limitations remain. Use OIDC and server-side authorization before operational deployment.
