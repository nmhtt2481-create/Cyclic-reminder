import json
from pathlib import Path

DEFAULTS = {
    "interval_minutes": 60,
    "active_hours_enabled": True,
    "active_from": "10:00",
    "active_to": "22:00",
    "image_path": "",
    "sound_path": "",
}

def settings_path() -> Path:
    try:
        from kivy.app import App
        return Path(App.get_running_app().user_data_dir) / "app_settings.json"
    except Exception:
        return Path(__file__).with_name("app_settings.json")

def load_settings() -> dict:
    path = settings_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {**DEFAULTS, **data}
    except (OSError, ValueError):
        return DEFAULTS.copy()

def save_settings(data: dict) -> None:
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({**DEFAULTS, **data}, ensure_ascii=False, indent=2), encoding="utf-8")
