import json
import os
from typing import Any, Dict

SESSION_FILE = "session_state.json"


def save_session(data: Dict[str, Any]) -> None:
    """Save session state to a JSON file so it survives server restarts."""
    try:
        with open(SESSION_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Session save failed: {e}")


def load_session() -> Dict[str, Any]:
    """Load session state from JSON file if it exists."""
    if not os.path.exists(SESSION_FILE):
        return {}
    try:
        with open(SESSION_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def clear_session() -> None:
    """Delete the session file."""
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)