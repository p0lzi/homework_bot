import logging
import logging.config
import sys
import time
from http import HTTPStatus

import handlers
import requests
import telegram
from exceptions import (
    APIConnectionError, EmptyResponseFromAPI, IncorrectAnswerFromAPI,
    TelegramConnectionError)
from setting import PRACTICUM_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_TOKEN

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

# Common logger configuration
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler(
    filename='homework.log',
    mode='w',
    encoding='utf-8'
)
telegram_handler = handlers.TelegramBotHandler()
telegram_handler.setLevel(logging.ERROR)
logging.basicConfig(
    handlers=(console_handler, file_handler, telegram_handler),
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(lineno)d %(message)s'
)


def send_message(bot, message):
    """Sends a message to the Telegram chat."""
    try:
        bot.sendMessage(chat_id=TELEGRAM_CHAT_ID, text=message)
    except telegram.error.TelegramError:
        raise TelegramConnectionError("Сбой при отправке сообщений в Telegram")
    else:
        logging.info("Успешная отправка сообщения в Telegram.")


def get_api_answer(current_timestamp):
    """Makes a request to the only endpoint of the API service."""
    request_kwargs = {'url': ENDPOINT,
                      'headers': HEADERS,
                      'params': {
                          'from_date': current_timestamp or int(time.time())
                      }}
    logging.info(f'Запрос к API {request_kwargs.get("url")}')
    try:
        response = requests.get(**request_kwargs)
        if response.status_code != HTTPStatus.OK:
            raise IncorrectAnswerFromAPI(
                f"Неверный ответ от API:\n{response.text}"
            )
        return response.json()
    except Exception:
        raise APIConnectionError(
            ("Ошибка подключение к API\nurl= {url}\nheaders= {headers}\n"
             "params= {params}").format(**request_kwargs))


def check_response(response):
    """Checks the API response for correctness."""
    logging.info("Проверка ответа API")
    if not isinstance(response, dict):
        raise TypeError("Ответ от API имеет некорректный тип.")
    homeworks = response.get('homeworks')
    if not homeworks:
        raise EmptyResponseFromAPI(
            "Отсутствие ключа 'homeworks' или  в ответе API."
        )
    if not isinstance(homeworks, list):
        raise KeyError(
            ("Ключ 'homeworks' в ответе от API домашняя работа приходят"
             "не в виде списка")
        )
    return homeworks


def parse_status(homework):
    """Gets status about specific homework."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    verdict = VERDICTS.get(homework_status)
    if not homework_name:
        raise KeyError("Отсутствие ключа 'homework_name' в ответе API.")
    if not homework_status:
        raise KeyError("Отсутствие ключа 'status' в ответе API.")
    if not verdict:
        raise ValueError(
            "Недокументированный статус домашней работы в ответе от API"
        )
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Checks the availability of environment variables."""
    if all((TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, PRACTICUM_TOKEN)):
        return True
    logging.critical("Отсутствует обязательные переменные окружения.")
    return False


def main():
    """The main logic of the bot."""
    if check_tokens():
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
    else:
        sys.exit("Отсутствует обязательные переменные окружения.")
    current_timestamp = int(time.time())
    # Решил использовать переменную str так, как на выходе функции
    # parse_status строка (подготовленное сообщение для отправки в Telegram)
    prev_message = ''
    while True:
        try:

            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks:
                for homework in homeworks:
                    message = parse_status(homework)
                    if message != prev_message:
                        send_message(bot, message)
                        prev_message = message
                    else:
                        logging.debug(
                            ("Сообщение не отправлено в Телеграмм, "
                             "было отправлено ранее"))
            else:
                logging.debug("В ответе нет новых статусов.")
        # У меня отправка логов в Telegram организовано на уровне logging
        # в TelegramBotHandler туда отправляется все сообщение уровня ERROR
        # и выше
        except Exception as error_message:
            # Проверка отправки повторных сообщений об ошибках в модуле
            # handlers в классе TelegramBotHandler
            logging.exception(error_message)
            time.sleep(RETRY_TIME)
        else:
            logging.debug("Цикл отработан без исключений")
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
