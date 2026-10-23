# Earthy interface update

Warm paper background, olive text and accents, terracotta buttons, Georgia serif headings, an original food-crate SVG, subtle texture, softer cards, a rescue-progress strip and warmer section headings.

Design references and reused tokens are documented in DESIGN_CREDITS.md. No new package dependencies, hosted fonts or remote artwork were added. Backend behavior and approval controls are unchanged.

## Load the update

If the previous app is running, stop it with Ctrl+C in its terminal. Start it again using `launch.bat`, or:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Then refresh the browser. A restart is needed for the new theme, and for previews launched with file watching disabled. SQLite data is retained.

`design-preview.html` is a standalone visual layout sample you can open locally. It is explicitly a static design preview; its controls do not execute the recovery workflow. Use Streamlit for the functioning application.

## Verification scope

The updated Python source was syntax-checked. The prior complete application suite passed 31 tests before this styling update. The latest UI test and preview-server runs were blocked by this session's Windows sandbox loopback restrictions, so the refreshed design has not been visually verified in the live app here. No new passing UI-test result is claimed. The earlier `preview.png` depicts the previous interface and is omitted from the refreshed ZIP to avoid confusion.
