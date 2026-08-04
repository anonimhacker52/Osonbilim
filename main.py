import json
import os
import glob
import re
from kivy.clock import Clock
from kivy.utils import platform
from kivy.properties import StringProperty, NumericProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.list import MDList

DATA_FILE = "progress.json"

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

class SplashScreen(MDScreen):
    def on_enter(self):
        Clock.schedule_once(self.go_to_menu, 2.5)
    
    def go_to_menu(self, dt):
        self.manager.current = 'menu'

class MenuScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lessons_data = []
        self.progress_data = self.load_progress()
        self.load_lessons()
    
    def load_lessons(self):
        lessons_folder = "darslar"
        if os.path.exists(lessons_folder):
            for fayl in sorted(glob.glob(os.path.join(lessons_folder, "*.json"))):
                with open(fayl, 'r', encoding='utf-8') as f:
                    self.lessons_data.append(json.load(f))
    
    def load_progress(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"completed_lessons": [], "total_xp": 0}
    
    def save_progress(self):
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.progress_data, f, ensure_ascii=False, indent=2)
    
    def on_enter(self):
        self.update_lessons_list()
    
    def update_lessons_list(self):
        lessons_list = self.ids.lessons_list
        lessons_list.clear_widgets()
        
        for idx, lesson in enumerate(self.lessons_data):
            lesson_num = idx + 1
            is_completed = lesson_num in self.progress_data["completed_lessons"]
            
            card = MDCard(
                orientation="vertical",
                padding="15dp",
                spacing="5dp",
                size_hint_y=None,
                height="90dp",
                radius=[15],
                elevation=3,
                md_bg_color=(0.2, 0.7, 0.3, 1) if is_completed else (1, 1, 1, 0.9) if MDApp.get_running_app().theme_cls.theme_style == "Light" else (0.2, 0.2, 0.3, 0.9),
            )
            
            title = MDLabel(
                text=f"{lesson['title']}",
                font_style="H6",
                theme_text_color="Custom",
                text_color=(1, 1, 1, 1) if is_completed else None,
            )
            
            words_count = MDLabel(
                text=f"{len(lesson['words'])} ta so'z",
                font_style="Body2",
                theme_text_color="Custom",
                text_color=(1, 1, 1, 0.8) if is_completed else None,
            )
            
            status = MDLabel(
                text="? Tugatilgan" if is_completed else "?? Boshlash",
                font_style="Caption",
                theme_text_color="Custom",
                text_color=(1, 1, 1, 1) if is_completed else (0.2, 0.5, 0.9, 1),
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
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_lesson_idx = 0
        self.current_word_idx = 0
        self.current_example_idx = 0
        self.lesson_data = None
        self.attempts = 0
        self.correct_count = 0
        self.total_examples = 0
        self.xp_earned = 0
        self.showing_word = True
    
    def load_lesson(self, idx):
        self.current_lesson_idx = idx
        self.current_word_idx = 0
        self.current_example_idx = 0
        self.attempts = 0
        self.correct_count = 0
        self.xp_earned = 0
        self.showing_word = True
        
        app = MDApp.get_running_app()
        self.lesson_data = app.menu_screen.lessons_data[idx]
        self.total_examples = sum(len(w['examples']) for w in self.lesson_data['words'])
        self.update_display()
    
    def update_display(self):
        if self.showing_word:
            self.show_word()
        else:
            self.show_example()
    
    def show_word(self):
        word = self.lesson_data['words'][self.current_word_idx]
        self.ids.word_title.text = f"{self.lesson_data['title']} - {self.current_word_idx + 1}/{len(self.lesson_data['words'])} so'z"
        self.ids.word_uz.text = word['uz']
        self.ids.word_en.text = word['en']
        self.ids.example_text.text = "Bu so'zni yodlab oling"
        self.ids.answer_input.text = ""
        self.ids.answer_input.disabled = True
        self.ids.check_btn.disabled = True
        self.ids.next_btn.text = "Tayyor, boshladik!"
        self.ids.feedback.text = ""
        self.ids.progress_bar.value = (self.current_word_idx / len(self.lesson_data['words'])) * 100
    
    def show_example(self):
        word = self.lesson_data['words'][self.current_word_idx]
        example = word['examples'][self.current_example_idx]
        self.ids.word_title.text = f"{self.lesson_data['title']} - {word['en']} | {self.current_example_idx + 1}/{len(word['examples'])} misol"
        self.ids.word_uz.text = example['uz']
        self.ids.word_en.text = ""
        self.ids.example_text.text = "Inglizcha tarjimasini yozing:"
        self.ids.answer_input.text = ""
        self.ids.answer_input.disabled = False
        self.ids.check_btn.disabled = False
        self.ids.next_btn.text = "Keyingi"
        self.ids.feedback.text = ""
        
        total_progress = self.current_word_idx + (self.current_example_idx / len(word['examples']))
        self.ids.progress_bar.value = (total_progress / len(self.lesson_data['words'])) * 100
    
    def clean_text(self, text):
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def check_answer(self):
        if self.showing_word:
            self.showing_word = False
            self.current_example_idx = 0
            self.attempts = 0
            self.update_display()
            return
        
        word = self.lesson_data['words'][self.current_word_idx]
        example = word['examples'][self.current_example_idx]
        user_answer = self.ids.answer_input.text.strip()
        correct_answer = example['en'].strip()
        
        if self.clean_text(user_answer) == self.clean_text(correct_answer):
            self.correct_count += 1
            xp = 10 if self.attempts == 0 else (5 if self.attempts == 1 else 2)
            self.xp_earned += xp
            self.ids.feedback.text = f"? To'g'ri! +{xp} XP"
            self.ids.feedback.theme_text_color = "Custom"
            self.ids.feedback.text_color = (0.2, 0.8, 0.4, 1)
            Clock.schedule_once(self.next_example, 1.2)
        else:
            self.attempts += 1
            if self.attempts >= 2:
                self.ids.feedback.text = f"? To'g'ri javob:\n{example['en']}\nEndi shuni yozing:"
                self.ids.feedback.theme_text_color = "Custom"
                self.ids.feedback.text_color = (1, 0.2, 0.2, 1)
                self.ids.answer_input.text = ""
            else:
                self.ids.feedback.text = "? Noto'g'ri, yana urinib ko'ring!"
                self.ids.feedback.theme_text_color = "Custom"
                self.ids.feedback.text_color = (1, 0.6, 0.2, 1)
    
    def next_example(self, dt=None):
        word = self.lesson_data['words'][self.current_word_idx]
        if self.current_example_idx < len(word['examples']) - 1:
            self.current_example_idx += 1
            self.attempts = 0
            self.update_display()
        else:
            if self.current_word_idx < len(self.lesson_data['words']) - 1:
                self.current_word_idx += 1
                self.showing_word = True
                self.update_display()
            else:
                self.finish_lesson()
    
    def next_btn_pressed(self):
        if self.showing_word:
            self.check_answer()
        else:
            self.next_example()
    
    def finish_lesson(self):
        app = MDApp.get_running_app()
        lesson_num = self.current_lesson_idx + 1
        if lesson_num not in app.menu_screen.progress_data["completed_lessons"]:
            app.menu_screen.progress_data["completed_lessons"].append(lesson_num)
        app.menu_screen.progress_data["total_xp"] += self.xp_earned
        app.menu_screen.save_progress()
        
        result_screen = self.manager.get_screen('result')
        result_screen.show_result(
            lesson_num=lesson_num,
            correct=self.correct_count,
            total=self.total_examples,
            xp=self.xp_earned
        )
        self.manager.current = 'result'
    
    def go_back(self):
        self.manager.current = 'menu'

class ResultScreen(MDScreen):
    def show_result(self, lesson_num, correct, total, xp):
        self.ids.result_title.text = f"?? {lesson_num}-dars tugadi!"
        self.ids.result_stats.text = f"? To'g'ri: {correct}/{total}\n?? Ball: +{xp} XP"
        
        app = MDApp.get_running_app()
        lesson = app.menu_screen.lessons_data[lesson_num - 1]
        
        if 'story' in lesson:
            self.ids.story_section.opacity = 1
            self.ids.story_text.text = lesson['story']['text']
        else:
            self.ids.story_section.opacity = 0
    
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
        sm = ScreenManager()
        sm.add_widget(SplashScreen(name='splash'))
        self.menu_screen = MenuScreen(name='menu')
        sm.add_widget(self.menu_screen)
        sm.add_widget(LessonScreen(name='lesson'))
        sm.add_widget(ResultScreen(name='result'))
        sm.add_widget(InfoScreen(name='info'))
        return sm
    
    def toggle_theme(self):
        if self.theme_cls.theme_style == "Light":
            self.theme_cls.theme_style = "Dark"
            self.theme_cls.primary_hue = "900"
        else:
            self.theme_cls.theme_style = "Light"
            self.theme_cls.primary_hue = "500"
            
    def open_link(self, url):
        open_url(url)

if __name__ == '__main__':
    OsonBilimApp().run()
