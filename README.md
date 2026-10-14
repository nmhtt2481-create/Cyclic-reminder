# Cyclic Reminder

Приложение на Kivy для циклических напоминаний. Приложение работает локально, хранит настройки в JSON-файле и поддерживает активное окно времени с точностью до минут.

## Возможности

- настройка интервала напоминаний в часах и минутах;
- активное окно напоминаний, например с `09:30` до `23:15`;
- поддержка окон, переходящих через полночь;
- режим работы круглосуточно;
- русскоязычный интерфейс;
- напоминание с изображением и зацикленным звуком;
- пауза звука и откладывание напоминания на пять минут;
- сохранение настроек между запусками приложения;
- сборка Android-приложения в формате `.apk`.

## Требования для запуска на компьютере

- Python 3.10 или новее;
- Kivy;
- KivyMD;
- Plyer.

Установка зависимостей:

```powershell
python -m pip install kivy kivymd plyer
```

Запуск:

```powershell
python main.py
```

## Сборка Android APK

Сборка выполняется в Linux или через WSL. Buildozer официально не предназначен для нативной сборки Windows.

Для Android-сборки нужны Linux или настроенный WSL2, Python 3, Buildozer и Java JDK. Android SDK/NDK Buildozer установит при первом запуске.

Установка Buildozer в Linux/WSL:

```bash
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip python3-venv
python3 -m pip install --user buildozer cython
```

Перейдите в каталог проекта и запустите debug-сборку:

```bash
cd /mnt/c/Users/user/Documents/Cyclic\ reminder
buildozer android debug
```

При первом запуске Buildozer скачает Android SDK/NDK и другие компоненты, поэтому сборка может занять значительное время.

Готовый APK появится в каталоге `bin/`. Найти его можно командой:

```bash
find bin -name '*.apk'
```

Установка на подключённое Android-устройство:

```bash
adb install -r bin/*.apk
```

Для повторной сборки после изменения исходников используйте `buildozer android debug`. Для полной очистки промежуточных файлов:

```bash
buildozer android clean
buildozer android debug
```

## Разрешения Android

Приложение запрашивает разрешения, необходимые для уведомлений, выбора медиафайлов, фоновой работы и точных напоминаний. На Android 13 и новее разрешение на уведомления нужно подтвердить при первом запуске.

## Настройки

Настройки сохраняются в приватный файл `app_settings.json` и содержат `interval_minutes`, `active_hours_enabled`, `active_from`, `active_to`, `image_path` и `sound_path`. Время начала и окончания хранится в формате `HH:MM`.

## Структура проекта

```text
Cyclic reminder/
├── main.py             # точка входа приложения
├── ui.py               # интерфейс Kivy
├── scheduler.py        # цикл планирования напоминаний
├── time_window.py      # проверка активного окна времени
├── settings.py         # загрузка и сохранение настроек
├── notifier.py         # звук и Android-уведомления
├── buildozer.spec      # конфигурация Android-сборки
└── README.md
```

## Проверка перед сборкой

```bash
python -m py_compile main.py ui.py scheduler.py time_window.py settings.py notifier.py
```
