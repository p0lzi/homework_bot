class NotForwardingInTelegram(Exception):
    pass


class ForwardingInTelegram(Exception):
    pass


class IncorrectAnswerFromAPI(ForwardingInTelegram):
    pass


class APIConnectionError(ForwardingInTelegram):
    pass


class TelegramConnectionError(NotForwardingInTelegram):
    pass
