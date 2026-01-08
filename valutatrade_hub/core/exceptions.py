# valutatrade_hub/core/exceptions.py

class ValutaTradeError(Exception):
    '''
    Базовое исключение
    '''
    pass

class InsufficientFundsError(ValutaTradeError):
    def __init__(self, code, available, required):
        self.code = code
        self.available = available
        self.required = required
        super().__init__(f"Недостаточно средств: доступно {available:.4f} {code}, требуется {required:.4f} {code}")

class CurrencyNotFoundError(ValutaTradeError):
    '''
    Исключение не найденной валюты
    '''
    def __init__(self, code):
        self.code = code
        super().__init__(f"Неизвестная валюта '{code}'")

class ApiRequestError(ValutaTradeError):
    '''
    Исключение ошибки при обращении к неизвестному API
    '''
    def __init__(self, reason):
        self.reason = reason
        super().__init__(f"Ошибка при обращении к внешнему API: {reason}")