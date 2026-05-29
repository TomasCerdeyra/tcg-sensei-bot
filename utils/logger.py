import json
from datetime import datetime

LOG_FILE = "data/usage_log.json"


def log_usage(user_id: int, tokens_in: int, tokens_out: int, command: str) -> None:
    entry = {
        "timestamp": datetime.now().isoformat(),
        "user_id": str(user_id),
        "command": command,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_usd": round(tokens_in * 0.000001 + tokens_out * 0.000005, 6),
    }
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        print(f"⚠️ Error logging: {e}")
