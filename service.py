"""Точка входа foreground-сервиса: крутит планировщик, пока UI свёрнут или закрыт.

Когда наступает время напоминания, сервис показывает уведомление (с полноэкранным
намерением, открывающим приложение) и оставляет флаг для UI, который затем
показывает картинку и проигрывает звук.
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
        manager.notify(NOTIFICATION_ID, builder.build())
    except Exception as exc:  # уведомление не должно ронять сервис
        print("reminder service: notify failed:", exc)


def on_reminder():
    bridge.mark_pending()
    notify()


def main():
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

    while True:
        bridge.write_state(scheduler.next_at)
        time.sleep(1)


if __name__ == "__main__":
    main()
