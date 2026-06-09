[app]
title = AL HAMD CADET SCHOOL
package.name = alhmadschool
package.domain = org.alhand
source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,ttf
version = 1.0

# Requirements optimize ki hain
requirements = python3,kivy,kivymd,pillow,requests

orientation = portrait
fullscreen = 0
android.permissions = INTERNET,ACCESS_NETWORK_STATE

# Build stability ke liye ye settings best hain
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True

android.archs = armeabi-v7a

log_level = 1
