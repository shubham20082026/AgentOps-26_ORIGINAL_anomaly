# Streamlit Cloud setup

1. Push this updated project to the connected GitHub repository.
2. Confirm the branch and entrypoint (main and app.py for a root deployment).
3. Open Manage app > Settings > Secrets and add your provider settings:

```toml
REROUTE_API_KEY = "YOUR_KEY_HERE"
REROUTE_MODEL = "gemini-3.5-flash-lite"
REROUTE_API_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
```

Never commit the real key. Windows-encrypted local credentials cannot be used on the Linux cloud host. Save Secrets and reboot the app if needed.

4. Click Test API connection.
5. Click Start fresh demo, select Happy path, and ingest it. In offline mode, investigate, review, enter dispatcher name, approve, reserve and accept both replies. Expect Confirmed.
6. Start another fresh demo and try LLM mode. API failures remain visible; offline retry is explicit.

## Evaluation lab

Compare the baseline and optional live LLM (uses provider quota) on identical inputs in isolated temporary databases. Results include correctness, latency, median/slowest time, tool calls, failures, the 30-second target and downloadable traces. Approval time is excluded.

Run concurrency and recovery checks for four competing cases, ten repeated booking commands, delayed confirmation, changing capacity and decline-driven replanning. Delay uses an injected clock. These checks test deterministic safeguards, not comparative LLM intelligence.

Repeat all six scenarios before claiming an advantage. API failures count as failures, not correct escalations.

## Persistence

SQLite persists on the current filesystem. Cloud rebuilds can replace local files. Guaranteed operational persistence requires external storage. Fresh demos preserve earlier files but are not authenticated private storage.

Official instructions: https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app/app-settings
