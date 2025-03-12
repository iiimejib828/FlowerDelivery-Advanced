import sys
import threading
import asyncio
import os
from django.apps import AppConfig

class BotConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bot"

    _bot_thread = None  # Храним ссылку на поток

    def ready(self):
        """Запускаем бота только один раз в главном процессе Django."""
        if "RUN_MAIN" not in os.environ:  # ✅ Django вызывает `ready()` дважды, `RUN_MAIN` фильтрует перезапуски
            return

        if "runserver" in sys.argv:
            if not BotConfig._bot_thread or not BotConfig._bot_thread.is_alive():
                BotConfig._bot_thread = threading.Thread(target=self.run_bot, daemon=True)
                BotConfig._bot_thread.start()

    def run_bot(self):
        """Запуск бота в отдельном потоке."""
        from bot.main import main
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())

    def is_reloading(self):
        """Проверяем, не перезапускает ли Django сервер автоматически."""
        try:
            from django.utils.autoreload import started_with_reloader
            return started_with_reloader()
        except ImportError:
            return False

