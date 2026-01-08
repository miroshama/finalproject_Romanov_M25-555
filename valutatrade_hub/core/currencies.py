# valutatrade_hub/core/currencies.py

from abc import ABC, abstractmethod

from .exceptions import CurrencyNotFoundError


class Currency(ABC):
    def __init__(self, name: str, code: str):
        if not name:
            raise ValueError("Имя не может быть пустым")
        if not (2 <= len(code) <= 5) or not code.isalpha():
            raise ValueError("Код должен содержать 2-5 букв")
        
        self.name = name
        self.code = code.upper()

    @abstractmethod
    def get_display_info(self) -> str:
        pass

class FiatCurrency(Currency):
    '''
    Государственные валюты
    '''
    def __init__(self, name, code, issuing_country):
        super().__init__(name, code)
        self.issuing_country = issuing_country

    def get_display_info(self) -> str:
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"

class CryptoCurrency(Currency):
    '''
    Крипто-валюты
    '''
    def __init__(self, name, code, algorithm, market_cap):
        super().__init__(name, code)
        self.algorithm = algorithm
        self.market_cap = market_cap

    def get_display_info(self) -> str:
        return f"[CRYPTO] {self.code} — {self.name} (Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})"

_CURRENCY_REGISTRY = {
    "USD": FiatCurrency("US Dollar", "USD", "United States"),
    "EUR": FiatCurrency("Euro", "EUR", "Eurozone"),
    "RUB": FiatCurrency("Russian Ruble", "RUB", "Russia"),
    "BTC": CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.12e12),
    "ETH": CryptoCurrency("Ethereum", "ETH", "Ethash", 3.5e11),
}

def get_currency(code: str) -> Currency:
    code = code.upper()
    if code not in _CURRENCY_REGISTRY:
        raise CurrencyNotFoundError(code)
    return _CURRENCY_REGISTRY[code]