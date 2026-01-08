# valutatrade_hub/parser_service/api_clients.py
from abc import ABC, abstractmethod
from datetime import datetime

import requests

from ..core.exceptions import ApiRequestError
from .config import parser_config


class BaseApiClient(ABC):
    @abstractmethod
    def fetch_rates(self) -> dict:
        '''
        Функция для форматирования в словарный вид
        '''
        pass

class CoinGeckoClient(BaseApiClient):
    def fetch_rates(self) -> dict:
        ids = ",".join(parser_config.CRYPTO_ID_MAP.values())
        vs_currency = parser_config.BASE_CURRENCY.lower()
        
        url = parser_config.COINGECKO_URL
        params = {
            "ids": ids,
            "vs_currencies": vs_currency
        }
        
        try:
            response = requests.get(url, params=params, timeout=parser_config.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            raise ApiRequestError(f"CoinGecko: {str(e)}")

        result = {}
        now = datetime.utcnow().isoformat()
        
        id_to_ticker = {v: k for k, v in parser_config.CRYPTO_ID_MAP.items()}
        
        for coin_id, rates in data.items():
            if coin_id in id_to_ticker:
                ticker = id_to_ticker[coin_id]
                rate = rates.get(vs_currency)
                if rate:
                    key = f"{ticker}_{parser_config.BASE_CURRENCY}"
                    result[key] = {
                        "rate": float(rate),
                        "updated_at": now,
                        "source": "CoinGecko"
                    }
        return result

class ExchangeRateApiClient(BaseApiClient):
    def fetch_rates(self) -> dict:
        key = parser_config.EXCHANGERATE_API_KEY
        if not key:
            raise ApiRequestError("ExchangeRate-API: API Key не найден в конфигурации")

        base = parser_config.BASE_CURRENCY
        url = f"{parser_config.EXCHANGERATE_API_URL}/{key}/latest/{base}"
        
        try:
            response = requests.get(url, timeout=parser_config.REQUEST_TIMEOUT)
            data = response.json()
            if response.status_code != 200 or data.get('result') != 'success':
                error_msg = data.get('error-type', 'Unknown error')
                raise ApiRequestError(f"ExchangeRate-API: {error_msg}")
        except requests.RequestException as e:
            raise ApiRequestError(f"ExchangeRate-API: {str(e)}")

        result = {}
        now = datetime.utcnow().isoformat()
        
        rates = data.get('conversion_rates', {}) 
        
        for fiat_code in parser_config.FIAT_CURRENCIES:
            if fiat_code in rates:
                key = f"{fiat_code}_{base}"
                result[key] = {
                    "rate": 1 / float(rates[fiat_code]),
                    "updated_at": now,
                    "source": "ExchangeRate-API"
                }
        return result