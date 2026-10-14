"""Связь UI-процесса с foreground-сервисом напоминаний (только Android).

Сервис работает в отдельном процессе, поэтому обмен идёт через файлы в
приватной папке приложения: сервис кладёт флаг «пришло напоминание» и время
следующего срабатывания, UI их читает. Модуль не импортирует kivy, чтобы его
можно было использовать внутри сервиса.
"""
import json
import os
from datetime import datetime
from pathlib import Path

from settings import settings_path

ANDROID = "ANDROID_ARGUMENT" in os.environ
SERVICE_NAME = "Reminder"  # совпадает с именем в buildozer.spec: services = reminder:...
REMINDER_SECONDS = 30  # сколько длятся звук, уведомление и картинка после срабатывания


def _dir() -> Path:
    return settings_path().parent


def _pending_file() -> Path:
    return _dir() / "pending_reminder"


def _stop_sound_file() -> Path:
    return _dir() / "stop_sound"


def _state_file() -> Path:
    return _dir() / "service_state.json"


# --- сторона сервиса ---------------------------------------------------------

def mark_pending():
    _pending_file().write_text(datetime.now().isoformat(), encoding="utf-8")


def pop_stop_request() -> bool:
    """True, если UI попросил остановить звук и убрать уведомление."""
    try:
        _stop_sound_file().unlink()
        return True
    except OSError:
        return False


def write_state(next_at):
    try:
        data = {"next_at": next_at.isoformat() if next_at else None}
        _state_file().write_text(json.dumps(data), encoding="utf-8")
    except OSError:
        pass


# --- сторона UI --------------------------------------------------------------

def pop_pending():
    """Время срабатывания, если сервис оставил непоказанное напоминание, иначе None.

    Флаг сбрасывается. Устаревшее (старше REMINDER_SECONDS) напоминание
    считается пропущенным и не возвращается.
    """
    path = _pending_file()
    try:
        fired = datetime.fromisoformat(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        fired = None
    try:
        path.unlink()
    except OSError:
        pass
    if fired and (datetime.now() - fired).total_seconds() < REMINDER_SECONDS:
        return fired
    return None


def request_stop_sound():
    """UI просит сервис остановить звук и убрать уведомление (кнопки в окне)."""
    try:
        _stop_sound_file().write_text("1", encoding="utf-8")
    except OSError:
        pass


def read_next_at():
    try:
        value = json.loads(_state_file().read_text(encoding="utf-8")).get("next_at")
        return datetime.fromisoformat(value) if value else None
    except (OSError, ValueError):
        return None


def _service_class():
    from jnius import autoclass
    activity = autoclass("org.kivy.android.PythonActivity").mActivity
    # p4a генерирует класс <package>.Service<Name> по имени из buildozer.spec
    return activity, autoclass(f"{activity.getPackageName()}.Service{SERVICE_NAME}")


def start_service(snooze_minutes=None):
    activity, service = _service_class()
    argument = json.dumps({"snooze": snooze_minutes} if snooze_minutes else {})
    service.start(activity, "", "Цикличное напоминание", "Напоминания работают в фоне", argument)


def stop_service():
    activity, service = _service_class()
    service.stop(activity)
    try:
        _state_file().unlink()
    except OSError:
        pass
