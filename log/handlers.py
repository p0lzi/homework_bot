import sys
from logging import Handler, LogRecord

import telegram

sys.path.append("..")
from setting import TELEGRAM_CHAT_ID, TELEGRAM_TOKEN


# Telegram handler class
class TelegramBotHandler(Handler):
    def __init__(self):
        super().__init__()
        self.token = TELEGRAM_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID

    def emit(self, record: LogRecord):
        bot = telegram.Bot(token=self.token)

        bot.sendMessage(chat_id=self.chat_id,
                        text=self.format(record))

    def format(self, record: LogRecord) -> str:
        text = super().format(record=record)
        return '⚠\n' + '\n'.join(text.split(maxsplit=3))

