#!/usr/bin/env python3
import json

from apps.api.app.adk_fleet import adk_runtime_status


if __name__ == "__main__":
    status = adk_runtime_status(enabled=True, model="gemini-2.5-flash")
    print(json.dumps(status, indent=2))
    if not status["installed"]:
        raise SystemExit("google-adk is not installed in this environment")
    if len(status["visible_agents"]) != 4:
        raise SystemExit("unexpected visible fleet topology")

