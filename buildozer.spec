[app]
title = Oson Bilim - Ingliz Tili
package.name = osonbilim
package.domain = org.osonbilim
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
source.exclude_dirs = .git,.github,bin,.buildozer
version = 1.0
requirements = python3,kivy==2.2.1,kivymd==1.1.1,pillow
orientation = portrait
fullscreen = 0
icon.filename = icon.png

android.permissions = INTERNET
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.archs = arm64-v8a
android.accept_sdk_license = True

p4a.branch = v2024.01.21

[buildozer]
log_level = 2
warn_on_root = 1
