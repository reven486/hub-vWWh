def public_projection(events: list[dict]) -> list[dict]:
    return [event for event in events if event.get("visibility") == "public"]
