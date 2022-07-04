import logging
import logging.config
import time
from http import HTTPStatus

import requests
import telegram
from exceptions import (
    CheckResponseHomeworksNotInList, CheckResponseNoHomeworks,
    GetNot200APIAnswer, ParseStatusUnknownStatus)
from setting import PRACTICUM_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_TOKEN

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

# Common logger configuration
logging.config.fileConfig('log/log.conf')
logger = logging.getLogger('root')


def send_message(bot, message):
    """Sends a message to the Telegram chat."""
    if bot.sendMessage(chat_id=TELEGRAM_CHAT_ID, text=message):
        logging.info("Успешная отправка сообщения в Telegram.")
    else:
        logging.error("Сбой при отправке сообщения в Telegram.")


def get_api_answer(current_timestamp):
    """Makes a request to the only endpoint of the API service."""
    timestamp = current_timestamp or int(time.time())
    # timestamp = 0
    params = {'from_date': timestamp}
    request = requests.get(ENDPOINT, headers=HEADERS, params=params)

    if request.status_code != HTTPStatus.OK:
        if request.status_code == HTTPStatus.NOT_FOUND:
            logging.error(f"Недоступен эндпоинта {ENDPOINT}")
        elif request.status_code == HTTPStatus.INTERNAL_SERVER_ERROR:
            logging.error(f"Ошибка работы эндпоинта {ENDPOINT}")
        else:
            logging.error(
                f"Ошибка {request.status_code} эндпоинта {ENDPOINT}."
            )
        raise GetNot200APIAnswer(
            f"Ошибка {request.status_code} эндпоинта {ENDPOINT}."
        )
    return request.json()


def check_response(response):
    """Checks the API response for correctness."""
    if not isinstance(response, dict):
        raise TypeError("Ответ от API имеет некорректный тип.")
    homeworks = response.get('homeworks')
    if not homeworks:
        logging.error("Отсутствие ключа 'homeworks' в ответе API.")
        raise CheckResponseNoHomeworks(
            "Отсутствие ключа 'homeworks' в ответе API."
        )
    elif not isinstance(homeworks, list):
        raise CheckResponseHomeworksNotInList(
            ("Ключ 'homeworks' в ответе от API домашняя работа приходят"
             "не в виде списка")
        )
    return homeworks


def parse_status(homework):
    """Gets status about specific homework."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    verdict = HOMEWORK_STATUSES.setdefault(homework_status)
    if not homework_name:
        logging.error("Отсутствие ключа 'homework_name' в ответе API.")
        raise KeyError("Отсутствие ключа 'homework_name' в ответе API.")
    if not homework_status:
        logging.error("Отсутствие ключа 'status' в ответе API.")
        raise KeyError("Отсутствие ключа 'status' в ответе API.")
    if not verdict:
        logging.error(("Недокументированный статус домашней работы, "
                       "обнаруженный в ответе API."))
        raise ParseStatusUnknownStatus(
            "Недокументированный статус домашней работы в ответе от API"
        )
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Checks the availability of environment variables.
    """
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
            homeworks = check_response(response)
            if homeworks:
                for homework in homeworks:
                    send_message(bot, parse_status(homework))
            else:
                logging.debug("В ответе нет новых статусов.")
            time.sleep(RETRY_TIME)
        except KeyError:
            logging.exception("Отсутствие ключа в ответе API.")
        except Exception:
            logging.exception("Сбой в работе программы")
            time.sleep(RETRY_TIME)
        else:
            logging.debug("Цикл отработан без исключений")


if __name__ == '__main__':
    main()
