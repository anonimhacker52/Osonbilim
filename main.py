"""Ishga tushirish fayli.

Ilova yiqilsa, xato matnini faylga yozadi. Keyingi ochilishda esa xatoni
ekranda ko'rsatadi, shunda uni skrinshot qilib yuborish mumkin.
Asosiy ilova kodi osonbilim_app.py faylida.
"""
import os
import sys
import traceback

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.environ.get("ANDROID_PRIVATE") or BASE_DIR
CRASH_LOG = os.path.join(LOG_DIR, "crash.log")
NATIVE_LOG = os.path.join(LOG_DIR, "native_crash.log")

_native_file = None


def read_logs():
    parts = []
    for path in (CRASH_LOG, NATIVE_LOG):
        try:
            if os.path.exists(path) and os.path.getsize(path) > 0:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    parts.append(f.read())
        except OSError:
            pass
    return "\n".join(parts).strip()


def clear_logs():
    for path in (CRASH_LOG, NATIVE_LOG):
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError:
            pass


def show_log(text):
    from kivy.app import App
    from kivy.core.window import Window
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.button import Button
    from kivy.uix.label import Label
    from kivy.uix.scrollview import ScrollView

    class ErrorApp(App):
        def build(self):
            root = BoxLayout(orientation="vertical", padding=10, spacing=10)
            title = Label(
                text="Ilova xatosi. Shu ekranni skrinshot qilib yuboring.",
                size_hint_y=None,
                height=60,
                halign="center",
                text_size=(Window.width - 30, None),
            )
            scroll = ScrollView()
            label = Label(
                text=text,
                size_hint_y=None,
                font_size="11sp",
                halign="left",
                valign="top",
                text_size=(Window.width - 30, None),
            )
            label.bind(texture_size=lambda inst, size: setattr(inst, "height", size[1]))
            scroll.add_widget(label)
            button = Button(
                text="Logni o'chirib, qayta urinish",
                size_hint_y=None,
                height=70,
                on_release=self.retry,
            )
            root.add_widget(title)
            root.add_widget(scroll)
            root.add_widget(button)
            return root

        def retry(self, *args):
            clear_logs()
            self.stop()

    ErrorApp().run()


def main():
    logs = read_logs()
    if logs:
        # Oxirgi qismi eng muhim (xato odatda oxirida bo'ladi)
        show_log(logs[-4000:])
        return

    global _native_file
    try:
        import faulthandler
        _native_file = open(NATIVE_LOG, "w")
        faulthandler.enable(file=_native_file, all_threads=True)
    except Exception:
        pass

    try:
        from osonbilim_app import OsonBilimApp
        OsonBilimApp().run()
    except Exception:
        try:
            with open(CRASH_LOG, "w", encoding="utf-8") as f:
                f.write(traceback.format_exc())
        except OSError:
            pass
        raise


if __name__ == "__main__":
    main()
