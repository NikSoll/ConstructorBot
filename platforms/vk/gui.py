import sys
import threading
import asyncio
import logging
from pathlib import Path
from tkinter import *
from tkinter import ttk, scrolledtext, messagebox
from tkinter import font as tkfont

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent.parent.parent

sys.path.append(str(BASE_DIR))

from core.utils.config_loader import load_config
from platforms.vk.adapter import VKBot


class BotGUI:
    def __init__(self):
        self.bot = None
        self.bot_thread = None
        self.is_running = False
        self.loop = None
        #загружаем конфиг
        config_path = BASE_DIR / 'config.json'
        self.config = load_config(str(config_path))

        if not self.config:
            messagebox.showerror("Ошибка", f"Не найден config.json\nИскал в:\n{config_path}")
            sys.exit(1)

        self._setup_ui()

    def _setup_ui(self):
        self.root = Tk()
        self.root.title("TheMomBot")
        self.root.geometry("700x600")
        self.root.minsize(600, 500)
        #ветовая схема
        self.colors = {
            'bg': '#0f172a',      #тёмно-синий фон
            'card': '#1e293b',    #карточки
            'accent': '#6366f1',  #акцентный (фиолетовый)
            'success': '#10b981', #зелёный
            'danger': '#ef4444',  #красный
            'text': '#f1f5f9',    #светлый текст
            'text_secondary': '#94a3b8'  #серый текст
        }
        self.root.configure(bg=self.colors['bg'])
        #шрифты
        self.font_title = tkfont.Font(family="Segoe UI", size=20, weight="bold")
        self.font_normal = tkfont.Font(family="Segoe UI", size=10)
        self.font_button = tkfont.Font(family="Segoe UI", size=11, weight="bold")
        self.font_log = tkfont.Font(family="Consolas", size=9)
        #основной контейнер с отступами
        main_frame = Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill=BOTH, expand=True, padx=30, pady=25)
        #заголовок
        title_frame = Frame(main_frame, bg=self.colors['bg'])
        title_frame.pack(fill=X, pady=(0, 25))
        Label(title_frame, text="🤖 TheMomBot", font=self.font_title,fg=self.colors['accent'], bg=self.colors['bg']).pack()
        Label(title_frame, text="VK бот", font=("Segoe UI", 12), fg=self.colors['text_secondary'],bg=self.colors['bg']).pack()
        #карточка с информацией
        info_frame = Frame(main_frame, bg=self.colors['card'], relief=FLAT, bd=0)
        info_frame.pack(fill=X, pady=(0, 20))
        #внутренние отступы карточки
        info_inner = Frame(info_frame, bg=self.colors['card'])
        info_inner.pack(fill=X, padx=20, pady=15)

        bot_name = self.config.get('name', 'Без названия')
        bot_type = self.config.get('bot_type', 'неизвестно')

        type_names = {
            'make': '💅 Запись на услуги',
            'shop': '🛍️ Интернет-магазин',
            'quiz': '🎯 Квиз-бот',
            'survey': '📋 Опросник',
            'mailer': '📢 Рассыльщик'
        }

        type_display = type_names.get(bot_type, bot_type)
        self._add_info_row(info_inner, "Название:", bot_name)
        self._add_info_row(info_inner, "Тип:", type_display)
        #статус
        status_frame = Frame(info_inner, bg=self.colors['card'])
        status_frame.pack(fill=X, pady=(10, 0))
        self.status_label = Label(status_frame, text="Остановлен",font=self.font_normal, fg=self.colors['danger'],bg=self.colors['card'])
        self.status_label.pack(side=LEFT, padx=(10, 0))
        #кнопки
        buttons_frame = Frame(main_frame, bg=self.colors['bg'])
        buttons_frame.pack(fill=X, pady=(0, 20))
        self.start_btn = Button(buttons_frame, text="▶️ Запустить бота",command=self.start_bot, bg=self.colors['success'], fg="white",font=self.font_button,padx=25, pady=10,bd=0, cursor="hand2",activebackground="#0d9488",activeforeground="white")
        self.start_btn.pack(side=LEFT, padx=(0, 15))
        self.stop_btn = Button(buttons_frame, text="⏹️ Остановить бота", command=self.stop_bot,bg=self.colors['danger'], fg="white",font=self.font_button,padx=25, pady=10,bd=0, cursor="hand2",state=DISABLED,activebackground="#dc2626",activeforeground="white")
        self.stop_btn.pack(side=LEFT)
        #лог
        log_frame = LabelFrame(main_frame, text="📝 Лог работы",font=self.font_normal, fg=self.colors['text'], bg=self.colors['card'],bd=1, relief=FLAT)
        log_frame.pack(fill=BOTH, expand=True)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, font=self.font_log, bg='#0a0f1a', fg='#a5f3c3',insertbackground='white', selectbackground=self.colors['accent'], bd=0,padx=10,pady=10)
        self.log_text.pack(fill=BOTH, expand=True, padx=2, pady=2)
        #статусбар
        self.statusbar = Label(self.root, text="✅ Готов к работе", bg=self.colors['card'], fg=self.colors['text_secondary'],font=("Segoe UI", 9),anchor=W, padx=15, pady=5)
        self.statusbar.pack(side=BOTTOM, fill=X)

        #логирования в GUI
        class TextHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget

            def emit(self, record):
                msg = self.format(record)
                def append():
                    self.text_widget.insert(END, msg + "\n")
                    self.text_widget.see(END)
                self.text_widget.after(0, append)

        handler = TextHandler(self.log_text)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(logging.INFO)

        #копир лог
        self.log_text.bind("<Control-c>", lambda e: self._copy_log())
        self.log_text.bind("<Button-3>", self._show_context_menu)

    def _add_info_row(self, parent, label, value):
        row = Frame(parent, bg=self.colors['card'])
        row.pack(fill=X, pady=3)

        Label(row, text=label,
              font=self.font_normal,
              fg=self.colors['text_secondary'],
              bg=self.colors['card'], width=10, anchor=W).pack(side=LEFT)

        Label(row, text=value,
              font=self.font_normal,
              fg=self.colors['text'],
              bg=self.colors['card'], anchor=W).pack(side=LEFT, fill=X, expand=True)

    def _copy_log(self):
        try:
            selected = self.log_text.get(SEL_FIRST, SEL_LAST)
            self.root.clipboard_clear()
            self.root.clipboard_append(selected)
        except:
            pass

    def _show_context_menu(self, event):
        menu = Menu(self.root, tearoff=0, bg=self.colors['card'], fg=self.colors['text'])
        menu.add_command(label="📋 Копировать", command=self._copy_log)
        menu.add_command(label="🗑️ Очистить лог", command=self._clear_log)
        menu.post(event.x_root, event.y_root)

    def _clear_log(self):
        self.log_text.delete(1.0, END)

    def _update_status(self, is_running: bool):
        self.is_running = is_running
        if is_running:
            self.status_label.config(text="Работает", fg=self.colors['success'])
            self.start_btn.config(state=DISABLED)
            self.stop_btn.config(state=NORMAL)
            self.statusbar.config(text="🟢 Бот запущен")
        else:
            self.status_label.config(text="Остановлен", fg=self.colors['danger'])
            self.start_btn.config(state=NORMAL)
            self.stop_btn.config(state=DISABLED)
            self.statusbar.config(text="⚫ Бот остановлен")

    def _run_bot(self):
        try:
            self.bot = VKBot(self.config)
            logging.info("Бот инициализирован")

            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

            self.loop.run_until_complete(self.bot.run())

        except Exception as e:
            logging.error(f"Ошибка при работе бота: {e}")
        finally:
            if self.loop:
                self.loop.close()
            self._update_status(False)

    def start_bot(self):
        #тут создаем отдельный поток для бота
        #если открывать его в главном потоке окно висит(
        if self.is_running:
            return

        self.bot_thread = threading.Thread(target=self._run_bot, daemon=True)
        self.bot_thread.start()
        self._update_status(True)
        logging.info("Бот запущен")

    def stop_bot(self):
        if not self.is_running:
            return

        if messagebox.askyesno("Подтверждение", "Остановить бота?"):
            self._update_status(False)
            logging.info("Бот остановлен")

    def run(self):
        #тут открываем в отдельном потоке
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.root.mainloop()

    def _on_closing(self):
        if self.is_running:
            if messagebox.askyesno("Выход", "Бот ещё работает. Остановить и выйти?"):
                self.stop_bot()
                self.root.destroy()
        else:
            self.root.destroy()


def main():
    app = BotGUI()
    app.run()


if __name__ == "__main__":
    main()