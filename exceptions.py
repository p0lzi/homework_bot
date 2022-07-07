# В задании было сказано про отправку всех логов уровня ERROR.
class IncorrectAnswerFromAPI(Exception):
    pass


class APIConnectionError(Exception):
    pass


class TelegramConnectionError(Exception):
    pass
