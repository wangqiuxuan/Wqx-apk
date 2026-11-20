import random
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, RoundedRectangle
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.window import Window

_sysrand = random.SystemRandom()

def random_face():
    return _sysrand.randint(1, 6)

LAYOUT = {
    1: [4],
    2: [0, 8],
    3: [0, 4, 8],
    4: [0, 2, 6, 8],
    5: [0, 2, 4, 6, 8],
    6: [0, 2, 3, 5, 6, 8],
}

class Pip(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._visible = False
        with self.canvas:
            self._color = Color(0.12, 0.12, 0.12, 1)
            self._ellipse = Ellipse()
        self.bind(pos=self._update, size=self._update)
        self._update()

    def _update(self, *args):
        d = min(self.width, self.height) * 0.75
        self._ellipse.size = (d, d)
        self._ellipse.pos = (self.center_x - d / 2, self.center_y - d / 2)

    def set_visible(self, v):
        self._color.a = 1 if v else 0

class DiceFace(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = 3
        self.rows = 3
        self.spacing = dp(2)
        self.padding = dp(8)
        self.pips = []
        for _ in range(9):
            p = Pip()
            self.pips.append(p)
            self.add_widget(p)

        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.bg = RoundedRectangle(radius=[dp(20)])
        self.bind(pos=self._update_bg, size=self._update_bg)
        self._update_bg()

    def _update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size

    def show(self, n):
        on = LAYOUT[n]
        for i, p in enumerate(self.pips):
            p.set_visible(i in on)

class DiceGame(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(20)
        self.spacing = dp(10)
        self.rolling = False
        self.total = 0
        self.counts = {i: 0 for i in range(1, 7)}
        self.history = []
        self._roll_event = None

        title = Label(
            text='摇骰子',
            font_size=dp(28),
            bold=True,
            size_hint_y=None,
            height=dp(50),
            color=(1, 1, 1, 1),
        )
        self.add_widget(title)

        dice_box = BoxLayout(size_hint_y=None, height=dp(230))
        dice_box.add_widget(Widget())
        self.dice = DiceFace(size_hint=(None, None), size=(dp(200), dp(200)))
        dice_box.add_widget(self.dice)
        dice_box.add_widget(Widget())
        self.add_widget(dice_box)

        self.roll_btn = Button(
            text='摇 一 摇',
            font_size=dp(20),
            bold=True,
            size_hint_y=None,
            height=dp(56),
            background_normal='',
            background_color=(0.03, 0.75, 0.4, 1),
        )
        self.roll_btn.bind(on_press=self.roll)
        self.add_widget(self.roll_btn)

        self.history_label = Label(
            text='历史: 暂无',
            font_size=dp(14),
            color=(0.7, 0.8, 0.9, 1),
            size_hint_y=None,
            height=dp(28),
        )
        self.add_widget(self.history_label)

        self.stats_label = Label(
            text='',
            font_size=dp(13),
            color=(0.8, 0.9, 1, 1),
            size_hint_y=None,
            height=dp(40),
        )
        self.add_widget(self.stats_label)

        self.toast_label = Label(
            text='',
            font_size=dp(15),
            bold=True,
            color=(1, 0.85, 0.3, 1),
            size_hint_y=None,
            height=dp(30),
        )
        self.add_widget(self.toast_label)

        self.dice.show(random_face())
        self.update_ui()

    def roll(self, *args):
        if self.rolling:
            return
        self.rolling = True
        self.roll_btn.disabled = True
        self.toast_label.text = ''

        final = random_face()
        self._roll_event = Clock.schedule_interval(
            lambda dt: self.dice.show(random_face()), 0.08
        )
        Clock.schedule_once(lambda dt: self._finish(final), 1.0)

    def _finish(self, final):
        Clock.unschedule(self._roll_event)
        self.dice.show(final)
        self.rolling = False
        self.roll_btn.disabled = False

        self.total += 1
        self.counts[final] += 1
        self.history.insert(0, final)
        if len(self.history) > 30:
            self.history.pop()

        if (
            len(self.history) >= 3
            and self.history[0] == self.history[1] == self.history[2]
        ):
            self.toast_label.text = f'三连 {final}！欧气爆棚 🎉'
            Clock.schedule_once(lambda dt: setattr(self.toast_label, 'text', ''), 2.0)

        self.update_ui()

    def update_ui(self):
        if self.history:
            self.history_label.text = '历史: ' + ' '.join(
                str(x) for x in self.history[:15]
            )
        else:
            self.history_label.text = '历史: 暂无'

        parts = [f'{i}点:{self.counts[i]}' for i in range(1, 7)]
        self.stats_label.text = '  '.join(parts) + f'  共{self.total}次'

class DiceApp(App):
    def build(self):
        Window.clearcolor = (0.05, 0.07, 0.1, 1)
        return DiceGame()

if __name__ == '__main__':
    DiceApp().run()
