# Debugger Guide

This project is set up to work with Visual Studio Code's debugger (debugpy).
Configuration can be found in `.vscode/launch.json`.

## Prerequisites
- VS Code with the Python extension
- A synced local environment from `uv sync --frozen --all-groups`
- Correct interpreter selected in VS Code

## Debugging Local Tests

Use the **Pytest (local)** configuration:

- Runs `pytest` directly under VS Code.
- Breakpoints in both `tests/` and `src/` will bind.
- No Docker required.

Steps:
1. Open the Run and Debug panel (Ctrl+Shift+D).
2. Select **Pytest (local)** and Activate the debugger.
3. Tests run in VS Code; breakpoints stop execution.
4. You can change the type of tests (unit or integration) by editing the path in `args` in the `launch.json` file.

## Debugging the App Inside Docker

When you are running the application via `docker compose`, you can use the **Python Debugger: Remote Attach** configuration:

1. Run the application with `docker compose up`.
2. Open the Run and Debug panel (Ctrl+Shift+D).
3. Select **Python Debugger: Remote Attach** and Activate the debugger.
4. Use the application as usual; the debugger will catch breakpoints and stop execution.
