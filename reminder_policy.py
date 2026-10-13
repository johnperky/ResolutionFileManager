from __future__ import annotations

from datetime import date
from typing import Literal


ReminderKind = Literal["rating", "support"]


def _integer(value, default: int, minimum: int = 0) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, result)


def normalise_state(state: dict | None) -> dict:
    source = state if isinstance(state, dict) else {}
    raw_dates = source.get("distinct_dates", [])
    dates: list[str] = []
    if isinstance(raw_dates, list):
        for value in raw_dates:
            try:
                parsed = date.fromisoformat(str(value)).isoformat()
            except (TypeError, ValueError):
                continue
            if parsed not in dates:
                dates.append(parsed)
    dates = sorted(dates)[-3:]
    return {
        "launch_count": _integer(source.get("launch_count"), 0),
        "distinct_dates": dates,
        "next_rating_launch": _integer(source.get("next_rating_launch"), 5, 1),
        "rating_disabled": bool(source.get("rating_disabled", False)),
        "next_support_launch": _integer(source.get("next_support_launch"), 11, 1),
        "support_disabled": bool(source.get("support_disabled", False)),
    }


def record_successful_launch(state: dict | None, today: date) -> dict:
    result = normalise_state(state)
    result["launch_count"] += 1
    value = today.isoformat()
    if value not in result["distinct_dates"]:
        result["distinct_dates"].append(value)
        result["distinct_dates"] = sorted(result["distinct_dates"])[-3:]
    return result


def eligible_reminder(state: dict | None) -> ReminderKind | None:
    value = normalise_state(state)
    if (
        not value["rating_disabled"]
        and value["launch_count"] >= value["next_rating_launch"]
        and len(value["distinct_dates"]) >= 3
    ):
        return "rating"
    if not value["support_disabled"] and value["launch_count"] >= value["next_support_launch"]:
        return "support"
    return None


def apply_reminder_choice(state: dict | None, reminder: ReminderKind, choice: str) -> dict:
    result = normalise_state(state)
    if reminder not in ("rating", "support"):
        raise ValueError(f"Unknown reminder: {reminder}")
    if reminder == "rating":
        if choice in ("rate", "never"):
            result["rating_disabled"] = True
        elif choice in ("later", "close"):
            result["next_rating_launch"] = result["launch_count"] + 10
        else:
            raise ValueError(f"Unknown rating choice: {choice}")
    else:
        if choice in ("open", "never"):
            result["support_disabled"] = True
        elif choice in ("later", "close"):
            result["next_support_launch"] = result["launch_count"] + 11
        else:
            raise ValueError(f"Unknown support choice: {choice}")
    return result


def set_reminder_enabled(state: dict | None, reminder: ReminderKind, enabled: bool) -> dict:
    result = normalise_state(state)
    if reminder == "rating":
        result["rating_disabled"] = not enabled
        if enabled:
            result["next_rating_launch"] = result["launch_count"] + 10
    elif reminder == "support":
        result["support_disabled"] = not enabled
        if enabled:
            result["next_support_launch"] = result["launch_count"] + 11
    else:
        raise ValueError(f"Unknown reminder: {reminder}")
    return result
