from datetime import datetime, timedelta
from threading import Event, Thread
from time_window import is_active, next_window_start

class ReminderScheduler:
    def __init__(self, get_settings, on_reminder):
        self.get_settings, self.on_reminder = get_settings, on_reminder
        self.stop_event, self.thread, self.next_at = Event(), None, None

    def start(self):
        if self.thread and self.thread.is_alive(): return
        self.stop_event.clear()
        self.thread = Thread(target=self._run, daemon=True)
        self.thread.start()

    def pause(self): self.stop_event.set()
    stop = pause

    def snooze(self, minutes=5):
        self.stop_event.set()
        self.next_at = datetime.now() + timedelta(minutes=minutes)
        self.stop_event.clear()
        self.thread = Thread(target=self._snooze_run, args=(minutes,), daemon=True)
        self.thread.start()

    def _snooze_run(self, minutes):
        if not self.stop_event.wait(minutes * 60):
            self.on_reminder()

    def _run(self):
        while not self.stop_event.is_set():
            cfg = self.get_settings(); now = datetime.now()
            if not is_active(now, cfg["active_hours_enabled"], cfg["active_from"], cfg["active_to"]):
                self.next_at = next_window_start(now, cfg["active_from"])
                self.stop_event.wait(max(1, (self.next_at - now).total_seconds()))
                continue
            delay = max(60, min(24 * 60 * 60, int(cfg["interval_minutes"]) * 60))
            self.next_at = now + timedelta(seconds=delay)
            if self.stop_event.wait(delay): break
            if is_active(datetime.now(), cfg["active_hours_enabled"], cfg["active_from"], cfg["active_to"]):
                self.on_reminder()
