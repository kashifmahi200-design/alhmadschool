[app]

# (str) Title of your application
title = AL HAMD CADET SCHOOL

# (str) Package name
package.name = alhmadschool

# (str) Package domain (needed for android/ios packaging)
package.domain = org.alhamd

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,kv,png,jpg,jpeg,ttf

# (str) Application versioning
version = 1.0

# (list) Application requirements
requirements = python3,kivy,kivymd,pillow,requests

# (str) Presplash of the application
# (str) Icon of the application

# (list) Supported orientations
orientation = portrait

# (bool) Indicate if the application should be fullscreen
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET,ACCESS_NETWORK_STATE

# (int) Target Android API
android.api = 33

# (int) Minimum API required
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25b

# (bool) If True, will accept the sdk license
android.accept_sdk_license = True

# (str) Log level
log_level = 1
