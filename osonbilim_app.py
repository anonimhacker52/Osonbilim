import json
import os
import glob
import re
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import platform
from kivy.properties import NumericProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.screenmanager import ScreenManager
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel

from lesson_logic import build_steps, is_correct

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def data_file_path():
    """Progress fayli ilovaning shaxsiy papkasida saqlanadi (Android uchun xavfsiz)."""
    app = MDApp.get_running_app()
    folder = app.user_data_dir if app else BASE_DIR
    try:
        os.makedirs(folder, exist_ok=True)
    except OSError:
        folder = BASE_DIR
    return os.path.join(folder, "progress.json")


def lesson_sort_key(path):
    """1-dars, 2-dars, ... 10-dars tartibida saralash (harf tartibida emas)."""
    match = re.match(r"(\d+)", os.path.basename(path))
    return int(match.group(1)) if match else 10 ** 9


def open_url(url):
    """URL ni Android yoki Kompyuterda ochish"""
    if platform == 'android':
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Intent = autoclass('android.content.Intent')
            Uri = autoclass('android.net.Uri')
            intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
            PythonActivity.mActivity.startActivity(intent)
        except Exception as e:
            print(f"Android URL xatosi: {e}")
    else:
        import webbrowser
        webbrowser.open(url)


class LessonCard(MDCard, ButtonBehavior):
    """Bosiladigan dars kartochkasi."""
    pass


class SplashScreen(MDScreen):
    def on_enter(self):
        Clock.schedule_once(self.go_to_menu, 2.5)

    def go_to_menu(self, dt):
        self.manager.current = 'menu'


class MenuScreen(MDScreen):
    # .kv fayl shu qiymatga bog'lanadi; o'zgarganda matn o'zi yangilanadi
    total_xp = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lessons_data = []
        self.progress_data = self.load_progress()
        self.load_lessons()
        self.migrate_progress()

    def load_lessons(self):
        lessons_folder = os.path.join(BASE_DIR, "darslar")
        if os.path.exists(lessons_folder):
            files = sorted(glob.glob(os.path.join(lessons_folder, "*.json")), key=lesson_sort_key)
            for fayl in files:
                try:
                    with open(fayl, 'r', encoding='utf-8') as f:
                        lesson = json.load(f)
                    # Progress dars tartib raqami emas, fayl nomi bo'yicha saqlanadi
                    lesson['_id'] = os.path.splitext(os.path.basename(fayl))[0]
                    self.lessons_data.append(lesson)
                except (OSError, ValueError) as e:
                    print(f"Dars o'qilmadi ({fayl}): {e}")

    def migrate_progress(self):
        """Eski saqlashni (raqamlar) yangisiga (fayl nomi + eng yaxshi ball) o'tkazadi."""
        p = self.progress_data
        p.setdefault("completed_lessons", [])
        p.setdefault("total_xp", 0)
        p.setdefault("lesson_xp", {})
        if "legacy_xp" not in p:
            # Eski versiyada yig'ilgan ball yo'qolmasin
            p["legacy_xp"] = p["total_xp"] if not p["lesson_xp"] else 0
        fixed = []
        for item in p["completed_lessons"]:
            if isinstance(item, int):
                if 1 <= item <= len(self.lessons_data):
                    item = self.lessons_data[item - 1]['_id']
                else:
                    continue
            if item not in fixed:
                fixed.append(item)
        p["completed_lessons"] = fixed
        self.recalc_total()

    def recalc_total(self):
        p = self.progress_data
        p["total_xp"] = p.get("legacy_xp", 0) + sum(p["lesson_xp"].values())
        self.total_xp = p["total_xp"]

    def load_progress(self):
        path = data_file_path()
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    return data
            except (OSError, ValueError):
                pass
        return {"completed_lessons": [], "total_xp": 0}

    def save_progress(self):
        try:
            with open(data_file_path(), 'w', encoding='utf-8') as f:
                json.dump(self.progress_data, f, ensure_ascii=False, indent=2)
        except OSError as e:
            print(f"Progress saqlanmadi: {e}")

    def on_enter(self):
        self.update_lessons_list()

    def update_lessons_list(self):
        lessons_list = self.ids.lessons_list
        lessons_list.clear_widgets()

        is_light = MDApp.get_running_app().theme_cls.theme_style == "Light"
        normal_title = (0.1, 0.1, 0.1, 1) if is_light else (1, 1, 1, 1)
        normal_sub = (0.4, 0.4, 0.4, 1) if is_light else (0.8, 0.8, 0.8, 1)
        white = (1, 1, 1, 1)

        for idx, lesson in enumerate(self.lessons_data):
            is_completed = lesson['_id'] in self.progress_data["completed_lessons"]

            if is_completed:
                bg = (0.2, 0.7, 0.3, 1)
            elif is_light:
                bg = (1, 1, 1, 0.9)
            else:
                bg = (0.2, 0.2, 0.3, 0.9)

            card = LessonCard(
                orientation="vertical",
                padding="15dp",
                spacing="5dp",
                size_hint_y=None,
                height="90dp",
                radius=[15],
                elevation=3,
                md_bg_color=bg,
            )

            title = MDLabel(
                text=f"{lesson['title']}",
                font_style="H6",
                theme_text_color="Custom",
                text_color=white if is_completed else normal_title,
            )

            words_count = MDLabel(
                text=f"{len(lesson['words'])} ta so'z",
                font_style="Body2",
                theme_text_color="Custom",
                text_color=(1, 1, 1, 0.8) if is_completed else normal_sub,
            )

            status = MDLabel(
                text="Tugatilgan" if is_completed else "Boshlash",
                font_style="Caption",
                theme_text_color="Custom",
                text_color=white if is_completed else (0.2, 0.5, 0.9, 1),
            )

            card.add_widget(title)
            card.add_widget(words_count)
            card.add_widget(status)
            card.bind(on_release=lambda x, idx=idx: self.start_lesson(idx))
            lessons_list.add_widget(card)

    def start_lesson(self, idx):
        lesson_screen = self.manager.get_screen('lesson')
        lesson_screen.load_lesson(idx)
        self.manager.current = 'lesson'

    def get_total_xp(self):
        return self.progress_data["total_xp"]


class LessonScreen(MDScreen):
    """Dars: so'z o'rgatiladi, keyin faqat o'tilgan so'zlardan iborat gaplar so'raladi."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_lesson_idx = 0
        self.lesson_data = None
        self.steps = []
        self.step_idx = 0
        self.attempts = 0
        self.correct_count = 0
        self.total_examples = 0
        self.xp_earned = 0
        self.answered = False      # shu misolga to'g'ri javob berilganmi
        self.finished = False
        self._pending = None       # 1.2 soniyadan keyingi avtomatik o'tish

    # ---- yordamchi ----
    def _cancel_pending(self):
        if self._pending is not None:
            self._pending.cancel()
            self._pending = None

    def _set_feedback(self, text, color):
        self.ids.feedback.text = text
        self.ids.feedback.theme_text_color = "Custom"
        self.ids.feedback.text_color = color

    # ---- darsni boshlash ----
    def load_lesson(self, idx):
        self._cancel_pending()
        self.current_lesson_idx = idx
        app = MDApp.get_running_app()
        self.lesson_data = app.menu_screen.lessons_data[idx]
        self.steps = build_steps(self.lesson_data)
        self.total_examples = sum(1 for s in self.steps if s[0] == 'example')
        self.step_idx = 0
        self.correct_count = 0
        self.xp_earned = 0
        self.finished = False
        self.show_step()

    def show_step(self):
        self._cancel_pending()
        step = self.steps[self.step_idx]
        title = self.lesson_data['title']
        words = self.lesson_data['words']
        self.attempts = 0
        self.answered = False
        self.ids.answer_input.text = ""
        self.ids.feedback.text = ""
        self.ids.progress_bar.value = (self.step_idx / len(self.steps)) * 100

        if step[0] == 'word':
            word = words[step[1]]
            self.ids.word_title.text = f"{title} - {step[1] + 1}/{len(words)} so'z"
            self.ids.word_uz.text = word['uz']
            self.ids.word_en.text = word['en']
            self.ids.example_text.text = "Bu so'zni yodlab oling"
            self.ids.answer_input.disabled = True
            self.ids.check_btn.disabled = True
            self.ids.next_btn.disabled = False
            self.ids.next_btn.text = "Tayyor, davom etamiz"
        else:
            number = sum(1 for s in self.steps[:self.step_idx + 1] if s[0] == 'example')
            self.ids.word_title.text = f"{title} - mashq {number}/{self.total_examples}"
            self.ids.word_uz.text = step[1]['uz']
            self.ids.word_en.text = ""
            self.ids.example_text.text = "Inglizcha tarjimasini yozing:"
            self.ids.answer_input.disabled = False
            self.ids.check_btn.disabled = False
            self.ids.next_btn.disabled = True      # javob bermasdan o'tib bo'lmaydi
            self.ids.next_btn.text = "Keyingi"

    # ---- javobni tekshirish ----
    def check_answer(self):
        if self.finished or self.answered or not self.steps:
            return
        step = self.steps[self.step_idx]
        if step[0] != 'example':
            return
        example = step[1]
        user_answer = self.ids.answer_input.text.strip()
        if not user_answer:
            self._set_feedback("Avval javobni yozing", (1, 0.6, 0.2, 1))
            return

        if is_correct(self.lesson_data, example, user_answer):
            self.answered = True
            self.correct_count += 1
            xp = 10 if self.attempts == 0 else (5 if self.attempts == 1 else 2)
            self.xp_earned += xp
            self._set_feedback(f"To'g'ri! +{xp} XP", (0.2, 0.8, 0.4, 1))
            self.ids.check_btn.disabled = True
            self.ids.next_btn.disabled = False
            self._cancel_pending()
            idx_now = self.step_idx
            self._pending = Clock.schedule_once(lambda dt: self._auto_next(idx_now), 1.2)
        else:
            self.attempts += 1
            if self.attempts >= 2:
                self._set_feedback(f"To'g'ri javob:\n{example['en']}\nEndi shuni yozing:", (1, 0.2, 0.2, 1))
                self.ids.answer_input.text = ""
            else:
                self._set_feedback("Noto'g'ri, yana urinib ko'ring!", (1, 0.6, 0.2, 1))

    # ---- keyingi bosqich ----
    def _auto_next(self, step_idx):
        """Avtomatik o'tish faqat o'sha misol hali ekranda bo'lsagina ishlaydi."""
        if step_idx == self.step_idx:
            self.next_step()

    def next_step(self, dt=None):
        """Bir martalik o'tish: avtomatik va tugma bosilishi to'qnashmaydi."""
        self._cancel_pending()
        if self.finished:
            return
        step = self.steps[self.step_idx]
        if step[0] == 'example' and not self.answered:
            return
        if self.step_idx < len(self.steps) - 1:
            self.step_idx += 1
            self.show_step()
        else:
            self.finish_lesson()

    def next_btn_pressed(self):
        self.next_step()

    def finish_lesson(self):
        if self.finished:
            return
        self.finished = True
        self._cancel_pending()
        app = MDApp.get_running_app()
        menu = app.menu_screen
        lesson = self.lesson_data
        lesson_id = lesson['_id']
        progress = menu.progress_data

        if lesson_id not in progress["completed_lessons"]:
            progress["completed_lessons"].append(lesson_id)
        # Ball faqat eng yaxshi natijadan oshgan qismi uchun qo'shiladi
        best = progress["lesson_xp"].get(lesson_id, 0)
        gained = max(0, self.xp_earned - best)
        if gained > 0:
            progress["lesson_xp"][lesson_id] = self.xp_earned
        menu.recalc_total()
        menu.save_progress()

        result_screen = self.manager.get_screen('result')
        result_screen.show_result(
            lesson=lesson,
            correct=self.correct_count,
            total=self.total_examples,
            xp=self.xp_earned,
            gained=gained,
            best=progress["lesson_xp"].get(lesson_id, 0),
        )
        self.manager.current = 'result'

    def on_leave(self, *args):
        self._cancel_pending()
        try:
            Window.release_all_keyboards()
        except Exception:
            pass

    def go_back(self):
        self._cancel_pending()
        self.manager.current = 'menu'


class ResultScreen(MDScreen):
    def show_result(self, lesson, correct, total, xp, gained, best):
        self.ids.result_title.text = f"{lesson['title']} tugadi!"
        if gained > 0:
            ball = f"Ball: +{gained} XP"
        else:
            ball = f"Ball oshmadi (eng yaxshi natija: {best} XP)"
        self.ids.result_stats.text = f"To'g'ri: {correct}/{total}\n{ball}"

        story = lesson.get('story')
        if story and story.get('text'):
            self.ids.story_section.opacity = 1
            self.ids.story_text.text = story['text']
        else:
            self.ids.story_section.opacity = 0
            self.ids.story_text.text = ""

    def skip_story(self):
        self.manager.current = 'menu'


class InfoScreen(MDScreen):
    pass


class OsonBilimApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme_cls.primary_palette = "DeepPurple"
        self.theme_cls.theme_style = "Light"
        self.menu_screen = None

    def build(self):
        self.theme_cls.material_style = "M3"
        # Klaviatura ochilganda yozish maydoni ko'rinib tursin
        Window.softinput_mode = "below_target"
        # Telefonning "orqaga" tugmasini ushlash (Android: 27-kod)
        Window.bind(on_keyboard=self.on_back_key)
        sm = ScreenManager()
        sm.add_widget(SplashScreen(name='splash'))
        self.menu_screen = MenuScreen(name='menu')
        sm.add_widget(self.menu_screen)
        sm.add_widget(LessonScreen(name='lesson'))
        sm.add_widget(ResultScreen(name='result'))
        sm.add_widget(InfoScreen(name='info'))
        return sm

    def on_back_key(self, window, key, *args):
        """Orqaga tugmasi: ichki ekranlardan menyuga qaytadi, menyuda ilovadan chiqadi."""
        if key == 27 and self.root is not None:
            if self.root.current in ('lesson', 'result', 'info'):
                self.root.current = 'menu'
                return True
        return False

    def go_to(self, screen_name):
        """Ekranni almashtirish (kv faylidagi lambda ichida tenglik yozib bo'lmaydi)."""
        self.root.current = screen_name

    def toggle_theme(self):
        if self.theme_cls.theme_style == "Light":
            self.theme_cls.theme_style = "Dark"
            self.theme_cls.primary_hue = "900"
        else:
            self.theme_cls.theme_style = "Light"
            self.theme_cls.primary_hue = "500"
        # Menyu kartochkalari ranglari yangilansin
        if self.menu_screen is not None:
            self.menu_screen.update_lessons_list()

    def open_link(self, url):
        open_url(url)


if __name__ == '__main__':
    OsonBilimApp().run()
