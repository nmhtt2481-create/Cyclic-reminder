"""Точка входа foreground-сервиса: крутит планировщик, пока UI свёрнут или закрыт.

Когда наступает время напоминания, сервис сам проигрывает звук и показывает
уведомление (с полноэкранным намерением, открывающим приложение), а также
оставляет флаг для UI, который по открытию приложения показывает картинку.
Через REMINDER_SECONDS секунд сервис останавливает звук и убирает уведомление.
"""
import json
import os
import time
from datetime import datetime, timedelta

import service_bridge as bridge
from scheduler import ReminderScheduler
from settings import load_settings

CHANNEL_ID = "reminders"
NOTIFICATION_ID = 2001

player = None
fired_at = None
wake_lock = None


def notify():
    try:
        from jnius import autoclass

        ctx = autoclass("org.kivy.android.PythonService").mService
        Build = autoclass("android.os.Build$VERSION")
        Builder = autoclass("android.app.Notification$Builder")
        PendingIntent = autoclass("android.app.PendingIntent")
        manager = ctx.getSystemService("notification")

        if Build.SDK_INT >= 26:
            Channel = autoclass("android.app.NotificationChannel")
            channel = Channel(CHANNEL_ID, "Напоминания", 4)  # IMPORTANCE_HIGH
            manager.createNotificationChannel(channel)
            builder = Builder(ctx, CHANNEL_ID)
        else:
            builder = Builder(ctx)

        launch = ctx.getPackageManager().getLaunchIntentForPackage(ctx.getPackageName())
        launch.addFlags(0x10000000 | 0x20000000)  # NEW_TASK | SINGLE_TOP
        pending = PendingIntent.getActivity(ctx, 0, launch, 0x08000000 | 0x04000000)  # UPDATE_CURRENT | IMMUTABLE

        builder.setSmallIcon(ctx.getApplicationInfo().icon)
        builder.setContentTitle("Напоминание")
        builder.setContentText("Пора выполнить действие")
        builder.setContentIntent(pending)
        builder.setFullScreenIntent(pending, True)
        builder.setAutoCancel(True)
        builder.setCategory("alarm")
        builder.setVisibility(1)  # VISIBILITY_PUBLIC: текст виден и на экране блокировки
        manager.notify(NOTIFICATION_ID, builder.build())
    except Exception as exc:  # уведомление не должно ронять сервис
        print("reminder service: notify failed:", exc)


def play_sound(path):
    global player
    stop_sound()
    if not path or not os.path.exists(path):
        return
    try:
        from jnius import autoclass

        player = autoclass("android.media.MediaPlayer")()
        player.setDataSource(path)
        player.setLooping(False)
        player.prepare()
        player.start()
    except Exception as exc:  # без звука картинка и уведомление всё равно работают
        print("reminder service: sound failed:", exc)
        player = None


def stop_sound():
    global player
    if player is None:
        return
    try:
        player.stop()
        player.release()
    except Exception:
        pass
    player = None


def cancel_notification():
    try:
        from jnius import autoclass

        ctx = autoclass("org.kivy.android.PythonService").mService
        ctx.getSystemService("notification").cancel(NOTIFICATION_ID)
    except Exception as exc:
        print("reminder service: cancel failed:", exc)


def acquire_wake_lock():
    """Не даёт процессору уснуть при выключенном экране, иначе таймер сервиса замирает."""
    global wake_lock
    try:
        from jnius import autoclass

        ctx = autoclass("org.kivy.android.PythonService").mService
        manager = ctx.getSystemService("power")
        wake_lock = manager.newWakeLock(1, "cyclicreminder:service")  # PARTIAL_WAKE_LOCK
        wake_lock.setReferenceCounted(False)
        wake_lock.acquire()
    except Exception as exc:  # без блокировки сервис всё равно работает при включённом экране
        print("reminder service: wake lock failed:", exc)


def end_reminder():
    global fired_at
    fired_at = None
    stop_sound()
    cancel_notification()


def on_reminder():
    global fired_at
    bridge.log("fired")
    bridge.pop_stop_request()  # старая просьба об остановке не должна глушить новый сигнал
    bridge.mark_pending()
    notify()
    play_sound(load_settings().get("sound_path", ""))
    fired_at = time.time()


def main():
    acquire_wake_lock()
    bridge.log("service start pid=%d wake_lock=%s" % (os.getpid(), wake_lock is not None))
    try:
        argument = json.loads(os.environ.get("PYTHON_SERVICE_ARGUMENT") or "{}")
    except ValueError:
        argument = {}
    scheduler = ReminderScheduler(load_settings, on_reminder)

    snooze = argument.get("snooze")
    if snooze:
        # Отложенное напоминание, затем обычный цикл продолжается.
        due = datetime.now() + timedelta(minutes=snooze)
        while datetime.now() < due:
            bridge.write_state(due)
            time.sleep(1)
        on_reminder()
    scheduler.start()

    last_tick = time.time()
    while True:
        now = time.time()
        if now - last_tick > 3:
            bridge.log("woke after %.0fs pause" % (now - last_tick))
        last_tick = now
        bridge.write_state(scheduler.next_at)
        if bridge.pop_stop_request() or (fired_at and time.time() - fired_at >= bridge.REMINDER_SECONDS):
            end_reminder()
        time.sleep(1)


if __name__ == "__main__":
    main()
