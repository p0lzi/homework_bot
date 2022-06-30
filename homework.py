import logging
import os
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

log_format = "%(asctime)s [%(levelname)s]\t%(message)s"

logging.basicConfig(
    format=log_format,
    level=logging.DEBUG,
    filename='homework.log',
    filemode='w'
)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(logging.Formatter(log_format))
logger = logging.getLogger(__name__)
logger.addHandler(stream_handler)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TOKEN')
TELEGRAM_CHAT_ID = os.getenv('MY_CHAT_ID')


RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Sends a message to the Telegram chat defined by the TELEGRAM_CHAT_ID
    environment variable"""
    if bot.sendMessage(chat_id=TELEGRAM_CHAT_ID, text=message):
        logging.info("Успешная отправка сообщения в Telegram.")
    else:
        logging.error("Сбой при отправке сообщения в Telegram.")


def get_api_answer(current_timestamp):
    """Makes a request to the only endpoint of the API service."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    request = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if request.status_code == HTTPStatus.NOT_FOUND:
        logging.error(f"Недоступен эндпоинта {ENDPOINT}")
    elif request.status_code == HTTPStatus.INTERNAL_SERVER_ERROR:
        logging.error(f"Ошибка работы эндпоинта {ENDPOINT}")
    elif request.status_code != HTTPStatus.OK:
        logging.error(f"Ошибка {request.status_code} эндпоинта {ENDPOINT}.")
    return request.json()


def check_response(response):
    """Checks the API response for correctness."""
    if not (homeworks := response.setdefault('homeworks')):
        logging.error(f"Отсутствие ключа 'homeworks' в ответе API.")
    return homeworks


def parse_status(homework):
    """Gets status about specific homework."""
    if not (homework_name := homework.setdefault('lesson_name')):
        logging.error(f"Отсутствие ключа 'lesson_name' в ответе API.")
    if not (homework_status := homework.setdefault('status')):
        logging.error(f"Отсутствие ключа 'status' в ответе API.")
    if not (verdict := HOMEWORK_STATUSES.setdefault(homework_status)):
        logging.error(("Недокументированный статус домашней работы, "
                       "обнаруженный в ответе API."))
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Checks the availability of environment variables that are necessary
    for work."""
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID and PRACTICUM_TOKEN:
        return True
    logging.critical("Отсутствует обязательные переменные окружения.")
    return False


def main():
    """The main logic of the bot."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    while True:
        try:
            current_timestamp = int(time.time())
            response = get_api_answer(current_timestamp)
            if homeworks := check_response(response):
                for homework in homeworks:
                    send_message(bot, parse_status(homework))
            else:
                logging.debug("В ответе нет новых статусов.")
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            time.sleep(RETRY_TIME)
        else:
            logging.debug("Цикл отработан без исключений")


if __name__ == '__main__':
    main()
