# valutatrade_hub/parser_service/config.py

import os
from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass
class ParserConfig:
    EXCHANGERATE_API_KEY: str = os.getenv("EXCHANGERATE_API_KEY")

    COINGECKO_URL: str = "https://api.coingecko.com/api/v3/simple/price"
    EXCHANGERATE_API_URL: str = "https://v6.exchangerate-api.com/v6"

    BASE_CURRENCY: str = "USD"
    FIAT_CURRENCIES: Tuple[str, ...] = ("EUR", "GBP", "RUB")
    
    CRYPTO_ID_MAP: Dict[str, str] = None
    
    def __post_init__(self):
        if self.CRYPTO_ID_MAP is None:
            self.CRYPTO_ID_MAP = {
                "BTC": "bitcoin",
                "ETH": "ethereum",
                "SOL": "solana",
            }

    RATES_FILE: str = "rates.json"
    HISTORY_FILE: str = "exchange_rates.json"

    REQUEST_TIMEOUT: int = 10

parser_config = ParserConfig()