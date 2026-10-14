from datetime import datetime, time, timedelta

def parse_hhmm(value: str) -> time:
    hour, minute = map(int, value.split(":", 1))
    if hour == 24 and minute == 0:
        return time.max
    return time(hour, minute)

def is_active(now: datetime, enabled: bool, start: str, end: str) -> bool:
    if not enabled:
        return True
    a, b, current = parse_hhmm(start), parse_hhmm(end), now.time()
    if a == b:
        return True
    return (a <= current < b) if a < b else (current >= a or current < b)

def next_window_start(now: datetime, start: str) -> datetime:
    target = parse_hhmm(start)
    result = now.replace(hour=target.hour, minute=target.minute, second=0, microsecond=0)
    if result <= now:
        result += timedelta(days=1)
    return result
