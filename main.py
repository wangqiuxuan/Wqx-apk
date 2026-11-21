import os
import math
import random
import threading
import ssl
from urllib.request import urlopen
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, RoundedRectangle
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.core.text import LabelBase

# ================= 全局字体配置 =================
HAS_CN = False

def load_font():
    global HAS_CN
    font_path = "chinese_font.ttf"
    
    sys_fonts = [
        '/system/fonts/NotoSansCJK-Regular.ttc',
        '/system/fonts/DroidSansFallback.ttf',
        '/system/fonts/NotoSansSC-Regular.otf'
    ]
    for f in sys_fonts:
        if os.path.exists(f):
            try:
                LabelBase.register(name='Roboto', fn_regular=f)
                HAS_CN = True
                return
            except Exception:
                pass
                
    if os.path.exists(font_path):
        try:
            LabelBase.register(name='Roboto', fn_regular=font_path)
            HAS_CN = True
            return
        except Exception:
            pass

    def download():
        global HAS_CN
        url = "https://cdn.jsdelivr.net/gh/googlefonts/noto-cjk@main/Sans/SubsetOTF/SC/NotoSansSC-Regular.otf"
        try:
            context = ssl._create_unverified_context()
            with urlopen(url, context=context, timeout=15) as response, open(font_path, 'wb') as out_file:
                out_file.write(response.read())
            if os.path.exists(font_path):
                LabelBase.register(name='Roboto', fn_regular=font_path)
                HAS_CN = True
                # 安全刷新界面
                def safe_update(dt):
                    app = App.get_running_app()
                    if app and app.root:
                        app.root.update_texts()
                Clock.schedule_once(safe_update, 0)
        except Exception as e:
            print("字体下载失败:", e)
            
    threading.Thread(target=download, daemon=True).start()

load_font()

# ================= 游戏逻辑 =================
_sysrand = random.SystemRandom()

def random_face():
    return _sysrand.randint(1, 6)

LAYOUT = {
    1: [4], 2: [0, 8], 3: [0, 4, 8],
    4: [0, 2, 6, 8], 5: [0, 2, 4, 6, 8], 6: [0, 2, 3, 5, 6, 8],
}

class Pip(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            self._color = Color(0.15, 0.15, 0.15, 1)
            self._ellipse = Ellipse()
        self.bind(pos=self._update, size=self._update)
        self._update()

    def _update(self, *args):
        d = min(self.width, self.height) * 0.8
        self._ellipse.size = (d, d)
        self._ellipse.pos = (self.center_x - d / 2, self.center_y - d / 2)

    def set_visible(self, v):
        self._color.a = 1 if v else 0

class DiceFace(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0, 0, 0, 0.4)
            self.shadow = RoundedRectangle(radius=[dp(24)])
            Color(1, 1, 1, 1)
            self.bg = RoundedRectangle(radius=[dp(24)])
            
        self.pips = []
        for _ in range(9):
            p = Pip()
            self.pips.append(p)
            self.add_widget(p)

        self.bind(pos=self._update, size=self._update)
        self._update()

    def _update(self, *args):
        self.shadow.pos = (self.x, self.y - dp(8))
        self.shadow.size = self.size
        self.bg.pos = self.pos
        self.bg.size = self.size
        
        w, h = self.width / 3, self.height / 3
        for i, p in enumerate(self.pips):
            row, col = i // 3, i % 3
            p.size = (w, h)
            p.pos = (self.x + col * w, self.y + (2 - row) * h)

    def show(self, n):
        on = LAYOUT[n]
        for i, p in enumerate(self.pips):
            p.set_visible(i in on)

class RoundedButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.background_normal = ''
        with self.canvas.before:
            self.bg_color = Color(0.03, 0.75, 0.4, 1)
            self.bg = RoundedRectangle(radius=[dp(30)])
        self.bind(pos=self._update, size=self._update, state=self._on_state)
        self._update()

    def _update(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size

    def _on_state(self, instance, value):
        if value == 'down':
            self.bg_color.rgba = (0.02, 0.6, 0.3, 1)
        else:
            self.bg_color.rgba = (0.03, 0.75, 0.4, 1)

class DiceGame(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(24)
        self.spacing = dp(16)
        self.rolling = False
        self.total = 0
        self.counts = {i: 0 for i in range(1, 7)}
        self.history = []
        
        self._anim_timer = None
        self._anim_time = 0
        self._final_face = 1
        self._orig_x = 0

        self.title_label = Label(font_size=dp(32), bold=True, size_hint_y=None, height=dp(60), color=(1, 1, 1, 1))
        self.add_widget(self.title_label)

        self.dice_box = BoxLayout(size_hint_y=None, height=dp(240))
        self.dice = DiceFace(size_hint=(None, None), size=(dp(200), dp(200)))
        self.dice_box.add_widget(Widget())
        self.dice_box.add_widget(self.dice)
        self.dice_box.add_widget(Widget())
        self.add_widget(self.dice_box)

        self.roll_btn = RoundedButton(font_size=dp(22), bold=True, size_hint_y=None, height=dp(64))
        self.roll_btn.bind(on_press=self.roll)
        self.add_widget(self.roll_btn)

        self.history_label = Label(font_size=dp(16), color=(0.7, 0.8, 0.9, 1), size_hint_y=None, height=dp(30))
        self.add_widget(self.history_label)

        self.stats_label = Label(font_size=dp(14), color=(0.6, 0.7, 0.8, 1), size_hint_y=None, height=dp(40))
        self.add_widget(self.stats_label)

        self.toast_label = Label(font_size=dp(18), bold=True, color=(1, 0.85, 0.3, 1), size_hint_y=None, height=dp(40))
        self.add_widget(self.toast_label)

        self.dice.show(random_face())
        self.update_texts()

    def update_texts(self):
        self.title_label.text = '摇 骰 子' if HAS_CN else 'DICE'
        self.roll_btn.text = '摇 一 摇' if HAS_CN else 'ROLL'
        self.update_ui()

    def roll(self, *args):
        if self.rolling: return
        self.rolling = True
        self.roll_btn.disabled = True
        self.toast_label.text = ''

        self._final_face = random_face()
        self._orig_x = self.dice.x
        self._anim_time = 0
        
        # 使用 Clock 定时器进行安全动画，避免使用 Animation 库导致闪退
        self._anim_timer = Clock.schedule_interval(self._update_animation, 1/60.0)

    def _update_animation(self, dt):
        if not self.rolling:
            return False

        self._anim_time += dt
        
        if self._anim_time < 1.0:
            # 前1秒：高频切换点数，同时左右摇摆
            if int(self._anim_time * 20) % 2 == 0:
                self.dice.show(random_face())
            
            # 手动计算正弦偏移
            offset = dp(15) * math.sin(self._anim_time * 30)
            self.dice.x = self._orig_x + offset
            
        elif self._anim_time < 1.3:
            # 1.0 到 1.3 秒：定格点数，回正位置（简单回弹效果）
            self.dice.show(self._final_face)
            progress = (self._anim_time - 1.0) / 0.3
            # 使用缓动公式实现回弹效果
            bounce = math.sin(progress * math.pi) * dp(10)
            self.dice.x = self._orig_x + bounce
        else:
            # 动画结束
            self.dice.x = self._orig_x
            self._finish()
            return False # 停止定时器

    def _finish(self):
        self.rolling = False
        self.roll_btn.disabled = False

        final = self._final_face
        self.total += 1
        self.counts[final] += 1
        self.history.insert(0, final)
        if len(self.history) > 30: self.history.pop()

        if len(self.history) >= 3 and self.history[0] == self.history[1] == self.history[2]:
            self.toast_label.text = f'三连 {final}！欧气爆棚 🎉' if HAS_CN else f'TRIPLE {final}! 🎉'
            Clock.schedule_once(self._clear_toast, 2.0)

        self.update_ui()

    def _clear_toast(self, dt):
        self.toast_label.text = ''

    def update_ui(self):
        if not HAS_CN:
            self.history_label.text = 'History: ' + ' '.join(str(x) for x in self.history[:15]) if self.history else 'History: None'
            parts = [f'{i}:{self.counts[i]}' for i in range(1, 7)]
            self.stats_label.text = '  '.join(parts) + f'  Total:{self.total}'
            return

        self.history_label.text = '历史: ' + ' '.join(str(x) for x in self.history[:15]) if self.history else '历史: 暂无'
        parts = [f'{i}点:{self.counts[i]}' for i in range(1, 7)]
        self.stats_label.text = '  '.join(parts) + f'  共{self.total}次'

class DiceApp(App):
    def build(self):
        Window.clearcolor = (0.1, 0.11, 0.15, 1)
        self.root_widget = DiceGame()
        return self.root_widget

if __name__ == '__main__':
    DiceApp().run()
