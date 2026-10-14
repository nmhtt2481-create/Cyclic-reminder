[app]
title = Cyclic Reminder
package.name = cyclicreminder
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,jpeg,wav,mp3,ogg,json
version = 1.0
requirements = python3,kivy,kivymd,plyer,pyjnius
orientation = portrait
fullscreen = 1
android.permissions = POST_NOTIFICATIONS,FOREGROUND_SERVICE_SPECIAL_USE,USE_FULL_SCREEN_INTENT,READ_MEDIA_IMAGES,READ_MEDIA_AUDIO,READ_EXTERNAL_STORAGE,FOREGROUND_SERVICE,SCHEDULE_EXACT_ALARM,WAKE_LOCK,RECEIVE_BOOT_COMPLETED
android.api = 35
android.minapi = 24
android.extra_manifest_application_arguments = manifest_application_args.xml
services = reminder:service.py:foreground:sticky:foregroundServiceType=specialUse
android.archs = arm64-v8a, armeabi-v7a
# android.add_src = android_src
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
