# Start the Correct OncoTwin Interface

The complete interface identifies itself as **OncoTwin 3D V10.0** and displays these tabs in the header:

```text
Live Mission | Cancer Twin | scRNA | Causal Observatory | Proof Galaxy | Generated Fix
```

If the page instead says **OncoTwin — DataHub Mission Control**, an older server is still running.

## Safest launch: use a new port

From the extracted `oncotwin-datahub-complete` directory:

```bash
chmod +x scripts/*.sh
ONCOTWIN_PORT=8081 bash scripts/12_local_demo.sh
```

Open a new browser tab at:

```text
http://localhost:8081
```

Verify the running version from a second terminal:

```bash
ONCOTWIN_PORT=8081 bash scripts/14_verify_ui_version.sh
```

The command must print:

```text
Verified OncoTwin UI v10.1.0 · mode: demo
```

## If you want to reuse port 8080

Return to the terminal that is running the old application and press `Ctrl+C`. Then start V10 normally:

```bash
bash scripts/12_local_demo.sh
```

Hard-refresh the browser after it starts:

- macOS Chrome: `Command + Shift + R`
- Windows/Linux Chrome: `Ctrl + Shift + R`

The V10 CSS and JavaScript URLs include a version marker to avoid stale browser assets. Three.js and OrbitControls are vendored inside the app, so all three 3D renderers remain independent of a CDN. The engines lazy-load, so a WebGL/GPU problem cannot disable live DataHub evidence or the other tabs.
