from pathlib import Path
from kivy.core.audio import SoundLoader

class Notifier:
    def __init__(self, on_done):
        self.on_done = on_done
        self.sound = None

    def play(self, path: str):
        if path and Path(path).exists():
            self.sound = SoundLoader.load(path)
            if self.sound:
                # Сигнал проигрывается один раз. Повторное воспроизведение
                # выполняется только по следующему срабатыванию планировщика.
                self.sound.loop = False
                self.sound.play()

    def pause(self):
        if self.sound:
            self.sound.stop()

    def stop(self):
        if self.sound:
            self.sound.stop()
            self.sound.unload()
            self.sound = None

    def android_notification(self, title="Напоминание"):
        try:
            from plyer import notification
            notification.notify(title=title, message="Пора выполнить действие", app_name="Цикличное напоминание")
        except Exception:
            pass
