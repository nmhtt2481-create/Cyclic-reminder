import os
from datetime import datetime
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.graphics import Color, Line
from kivy.metrics import dp
from settings import load_settings, save_settings
from scheduler import ReminderScheduler
from notifier import Notifier
import service_bridge as bridge

class VisibleCheckBox(CheckBox):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.after:
            Color(0.18, 0.28, 0.42, 1)
            self.border = Line(rectangle=(0, 0, 0, 0), width=1.4, joint="round")
        self.bind(pos=self._update_border, size=self._update_border)

    def _update_border(self, *_):
        inset = 1
        self.border.rectangle = (self.x + inset, self.y + inset, self.width - inset * 2, self.height - inset * 2)

class ReminderApp(App):
    def build(self):
        self.cfg = load_settings(); self.notifier = Notifier(self.show_reminder)
        # Эталон — десктопное окно ~800x630 (dp == px). На телефоне размеры задаются в dp,
        # а по вертикали растягиваются пропорционально высоте экрана, чтобы блок
        # занимал ту же долю экрана, что и в десктопной версии.
        vs = max(1.0, Window.height / (630 * dp(1)))
        vdp = self.vdp = lambda value: dp(value) * vs
        field_w = dp(40 if bridge.ANDROID else 52)
        self.root_box = BoxLayout(orientation="vertical", padding=vdp(12), spacing=vdp(8))
        self.status = Label(text="Остановлено", size_hint_y=None, height=vdp(32))
        stored_minutes = int(self.cfg["interval_minutes"])
        self.interval_hours = TextInput(text=str(stored_minutes // 60), hint_text="Часы", input_filter="int", multiline=False, halign="center")
        self.interval_minutes = TextInput(text=str(stored_minutes % 60), hint_text="Минуты", input_filter="int", multiline=False, halign="center")
        from_hour, from_minute = self.cfg["active_from"].split(":", 1)
        to_hour, to_minute = self.cfg["active_to"].split(":", 1)
        self.from_time = TextInput(text=from_hour.zfill(2), hint_text="ЧЧ", input_filter="int", multiline=False, halign="center", size_hint_x=None, width=field_w)
        self.from_minute = TextInput(text=from_minute.zfill(2), hint_text="ММ", input_filter="int", multiline=False, halign="center", size_hint_x=None, width=field_w)
        self.to_time = TextInput(text=to_hour.zfill(2), hint_text="ЧЧ", input_filter="int", multiline=False, halign="center", size_hint_x=None, width=field_w)
        self.to_minute = TextInput(text=to_minute.zfill(2), hint_text="ММ", input_filter="int", multiline=False, halign="center", size_hint_x=None, width=field_w)
        self.always = VisibleCheckBox(active=not self.cfg["active_hours_enabled"], size_hint=(None, None), size=(dp(38), dp(38)), color=(0.25, 0.55, 0.95, 1))
        for field in (self.interval_hours, self.interval_minutes):
            field.size_hint_x = None
            field.width = field_w
            field.bind(text=lambda widget, value: setattr(widget, "text", value[:2]) if len(value) > 2 else None)
        numeric_fields = (self.interval_hours, self.interval_minutes, self.from_time, self.from_minute, self.to_time, self.to_minute)
        for field in numeric_fields:
            field.bind(size=lambda widget, value: setattr(widget, "padding_y", max(0, (widget.height - widget.line_height) / 2)))
        for field in (self.from_time, self.from_minute, self.to_time, self.to_minute):
            field.bind(text=lambda widget, value: setattr(widget, "text", value[:2]) if len(value) > 2 else None)

        interval_title = Label(text="Интервал", halign="center", valign="middle")
        interval_title.bind(size=lambda widget, value: setattr(widget, "text_size", value))
        def fixed_label(text):
            label = Label(text=text, size_hint_x=None, halign="center", valign="middle")
            label.bind(texture_size=lambda widget, value: setattr(widget, "width", value[0]))
            return label

        spacer_width = dp(8 if bridge.ANDROID else 24)
        interval_row = BoxLayout(orientation="horizontal", size_hint=(None, None), width=0, height=vdp(42))
        interval_row.add_widget(fixed_label("Количество часов"))
        interval_row.add_widget(Label(text="   ", size_hint_x=None, width=spacer_width))
        interval_row.add_widget(self.interval_hours)
        interval_row.add_widget(Label(text="   ", size_hint_x=None, width=spacer_width))
        interval_row.add_widget(fixed_label("Количество минут"))
        interval_row.add_widget(Label(text="   ", size_hint_x=None, width=spacer_width))
        interval_row.add_widget(self.interval_minutes)
        interval_row.bind(minimum_width=lambda widget, value: setattr(widget, "width", value))
        interval_row.pos_hint = {"center_x": 0.5}
        self.root_box.add_widget(interval_title)
        self.root_box.add_widget(interval_row)

        active_title = Label(text="Активное окно времени работы напоминаний", halign="center", valign="middle")
        active_title.bind(size=lambda widget, value: setattr(widget, "text_size", value))
        active_row = BoxLayout(orientation="horizontal", size_hint=(None, None), width=0, height=vdp(42))
        active_row.add_widget(fixed_label("с"))
        active_row.add_widget(Label(text="   ", size_hint_x=None, width=spacer_width))
        active_row.add_widget(self.from_time)
        active_row.add_widget(Label(text="   ", size_hint_x=None, width=spacer_width))
        active_row.add_widget(self.from_minute)
        active_row.add_widget(Label(text="   ", size_hint_x=None, width=spacer_width))
        active_row.add_widget(fixed_label("до"))
        active_row.add_widget(Label(text="   ", size_hint_x=None, width=spacer_width))
        active_row.add_widget(self.to_time)
        active_row.add_widget(Label(text="   ", size_hint_x=None, width=spacer_width))
        active_row.add_widget(self.to_minute)
        active_row.bind(minimum_width=lambda widget, value: setattr(widget, "width", value))
        active_row.pos_hint = {"center_x": 0.5}
        self.root_box.add_widget(active_title)
        self.root_box.add_widget(active_row)
        row = BoxLayout(size_hint_y=None, height=vdp(42)); row.add_widget(self.always); row.add_widget(Label(text="Работать круглосуточно")); self.root_box.add_widget(row)
        for text, action in (("Старт", self.start), ("Пауза таймера", self.pause), ("Стоп", self.stop_all), ("Выбрать картинку", self.pick_image), ("Выбрать звук", self.pick_sound)):
            self.root_box.add_widget(Button(text=text, on_release=action, size_hint_y=None, height=vdp(44)))
        self.root_box.add_widget(self.status); self.scheduler = ReminderScheduler(lambda: self.cfg, self.show_reminder); Clock.schedule_interval(self.refresh, 1)
        return self.root_box

    def persist(self):
        hours = max(0, int(self.interval_hours.text or 0))
        minutes_part = max(0, min(59, int(self.interval_minutes.text or 0)))
        minutes = hours * 60 + minutes_part
        start_hour = max(0, min(23, int(self.from_time.text or 0)))
        start_minute = max(0, min(59, int(self.from_minute.text or 0)))
        end_hour = max(0, min(24, int(self.to_time.text or 0)))
        end_minute = max(0, min(59, int(self.to_minute.text or 0)))
        if end_hour == 24:
            end_minute = 0
        self.cfg.update(interval_minutes=max(1, min(1440, minutes)), active_hours_enabled=not self.always.active, active_from=f"{start_hour:02d}:{start_minute:02d}", active_to=f"{end_hour:02d}:{end_minute:02d}"); save_settings(self.cfg)
    def start(self, *_):
        self.persist()
        if bridge.ANDROID:
            self._request_notification_permission()
            self._restart_service()
        else:
            self.scheduler.start()
        self.status.text = "Запущено"
        if getattr(self, "start_minimize_event", None):
            self.start_minimize_event.cancel()
        self.start_minimize_event = Clock.schedule_once(lambda *_: self.minimize_app(), 5)

    def _request_notification_permission(self):
        try:
            from android.permissions import request_permissions
            request_permissions(["android.permission.POST_NOTIFICATIONS"])
        except Exception:
            pass

    def _restart_service(self, snooze_minutes=None):
        # Запущенный сервис повторно не стартует, поэтому сначала останавливаем его,
        # чтобы он перечитал настройки; старт чуть позже, чтобы остановка успела пройти.
        try:
            bridge.stop_service()
            Clock.schedule_once(lambda *_: bridge.start_service(snooze_minutes), 0.7)
        except Exception as exc:
            self.status.text = "Не удалось запустить сервис: " + str(exc)

    def _stop_timer(self):
        if bridge.ANDROID:
            try:
                bridge.stop_service()
            except Exception:
                pass
        else:
            self.scheduler.pause()

    def on_pause(self):
        # Пока приложение свёрнуто, таймеры Kivy стоят. Сбрасываем окно напоминания
        # и его таймеры, иначе просроченный таймер при возврате сразу свернёт
        # приложение, а новое напоминание не покажется (окно «ещё открыто»).
        for name in ("start_minimize_event", "reminder_close_event"):
            event = getattr(self, name, None)
            if event:
                event.cancel()
                setattr(self, name, None)
        if getattr(self, "active_popup", None):
            self.active_popup.dismiss()
            self.active_popup = None
        return True

    def on_resume(self):
        self.check_pending()

    def check_pending(self):
        # Сервис оставляет флаг, когда наступило время напоминания.
        if not bridge.ANDROID:
            return
        fired = bridge.pop_pending()
        if fired and not getattr(self, "active_popup", None):
            # Звук уже играет в сервисе; картинка живёт до конца 30-секундного окна.
            left = bridge.REMINDER_SECONDS - (datetime.now() - fired).total_seconds()
            self._show_reminder_ui(left)
    def pause(self, *_): self._stop_timer(); self.status.text = "Пауза"
    def stop_all(self, *_):
        self._stop_timer()
        self.notifier.stop()
        if getattr(self, "start_minimize_event", None):
            self.start_minimize_event.cancel()
            self.start_minimize_event = None
        if getattr(self, "active_popup", None):
            if getattr(self, "reminder_close_event", None):
                self.reminder_close_event.cancel()
                self.reminder_close_event = None
            self.active_popup.dismiss()
            self.active_popup = None
        self.status.text = "Остановлено"
        # «Стоп» завершает приложение полностью. Следующее напоминание
        # появится только после нового запуска приложения ярлыком.
        Clock.schedule_once(lambda *_: self.stop(), 0)

    def minimize_app(self):
        """Сворачивает приложение, не завершая его процесс."""
        try:
            from jnius import autoclass
            activity = autoclass("org.kivy.android.PythonActivity").mActivity
            activity.moveTaskToBack(True)
        except Exception:
            # На Windows/Linux сворачивание зависит от оконного менеджера;
            # отсутствие pyjnius не должно ломать кнопку «Стоп».
            try:
                from kivy.core.window import Window
                Window.minimize()
            except Exception:
                pass
    def refresh(self, *_):
        self.check_pending()
        next_at = bridge.read_next_at() if bridge.ANDROID else self.scheduler.next_at
        if next_at: self.status.text = "До следующего: " + str(max(0, int((next_at - datetime.now()).total_seconds()))) + " сек."
    def pick_image(self, *_):
        self._pick("image_path", "Выбор изображения", ("*.png", "*.jpg", "*.jpeg", "*.PNG", "*.JPG", "*.JPEG"), "Pictures/Gallery", ("READ_MEDIA_IMAGES",))
    def pick_sound(self, *_):
        self._pick("sound_path", "Выбор звука", ("*.mp3", "*.wav", "*.ogg", "*.MP3", "*.WAV", "*.OGG"), "Music", ("READ_MEDIA_AUDIO",))

    def _pick(self, key, title, filters, subdir, media_permissions):
        if not bridge.ANDROID:
            return self._open_picker(key, title, filters, None)
        open_picker = lambda *_: Clock.schedule_once(lambda *_: self._open_picker(key, title, filters, subdir))
        try:
            from android.permissions import check_permission, request_permissions
            # READ_MEDIA_* действуют с Android 13, READ_EXTERNAL_STORAGE — на более старых.
            wanted = ["android.permission." + name for name in (*media_permissions, "READ_EXTERNAL_STORAGE")]
            missing = [name for name in wanted if not check_permission(name)]
            if missing:
                # Окно открывается после ответа пользователя на запрос доступа к файлам.
                request_permissions(missing, open_picker)
                return
        except Exception:
            pass
        open_picker()

    def _storage_dir(self, subdir):
        """Папка внутреннего накопителя (например, Pictures/Gallery); если её нет — корень накопителя."""
        try:
            from android.storage import primary_external_storage_path
            root = primary_external_storage_path()
        except Exception:
            root = "/storage/emulated/0"
        path = os.path.join(root, subdir)
        return path if os.path.isdir(path) else root

    def _open_picker(self, key, title, filters, subdir):
        from kivy.uix.filechooser import FileChooserListView
        options = {"path": self._storage_dir(subdir)} if subdir else {}
        chooser = FileChooserListView(filters=list(filters), **options)
        box = BoxLayout(orientation="vertical", spacing=self.vdp(8))
        box.add_widget(chooser)
        b = Button(text="Выбрать", size_hint_y=None, height=self.vdp(44))
        box.add_widget(b)
        pop = Popup(title=title, content=box, size_hint=(.95, .9))
        b.bind(on_release=lambda *_: (self.cfg.update({key: chooser.selection[0]} if chooser.selection else {}), save_settings(self.cfg), pop.dismiss()))
        pop.open()
    def show_reminder(self):
        # Popup и виджеты Kivy должны создаваться только в главном потоке.
        Clock.schedule_once(lambda *_: self._show_reminder_ui())

    def _stop_alert(self):
        """Останавливает звук (на Android он играет в сервисе) и убирает уведомление."""
        self.notifier.stop()
        if bridge.ANDROID:
            bridge.request_stop_sound()

    def _show_reminder_ui(self, seconds=None):
        if getattr(self, "active_popup", None):
            self.active_popup.dismiss()
            self.active_popup = None
        if not bridge.ANDROID: self.notifier.play(self.cfg.get("sound_path", ""))
        box = BoxLayout(orientation="vertical", spacing=self.vdp(8));
        if self.cfg.get("image_path"):
            box.add_widget(Image(source=self.cfg["image_path"], allow_stretch=True, keep_ratio=True))
        buttons = BoxLayout(orientation="vertical", size_hint_y=None, height=self.vdp(44) * 3 + self.vdp(8) * 2, spacing=self.vdp(8)); ok=Button(text="Ок / Я сделал"); pause_sound=Button(text="Пауза звука"); snooze=Button(text="Отложить +5 минут"); buttons.add_widget(ok); buttons.add_widget(pause_sound); buttons.add_widget(snooze); box.add_widget(buttons)
        pop = Popup(title="Напоминание", content=box, size_hint=(1,1), auto_dismiss=False)
        self.active_popup = pop
        # Подтверждение закрывает только текущее окно и сворачивает UI;
        # расписание напоминаний при этом не прерывается.
        ok.bind(on_release=lambda *_: self._close_reminder_ui(pop))
        pause_sound.bind(on_release=lambda *_: (self.notifier.pause(), bridge.request_stop_sound() if bridge.ANDROID else None))
        snooze.bind(on_release=lambda *_: (self._stop_alert(), pop.dismiss(), setattr(self, "active_popup", None), self._restart_service(5) if bridge.ANDROID else self.scheduler.snooze(5)))
        if not bridge.ANDROID: self.notifier.android_notification()
        pop.open()
        delay = bridge.REMINDER_SECONDS if seconds is None else max(0, seconds)
        self.reminder_close_event = Clock.schedule_once(lambda *_: self._close_reminder_ui(pop), delay)

    def _close_reminder_ui(self, pop):
        """Закрывает напоминание и сворачивает приложение.

        Метод вызывается сразу по кнопке «Ок / Я сделал» или автоматически
        через 30 секунд, если кнопка не была нажата.
        """
        if getattr(self, "active_popup", None) is not pop:
            return
        self._stop_alert()
        pop.dismiss()
        self.active_popup = None
        self.reminder_close_event = None
        self.minimize_app()
