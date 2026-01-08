# valutatrade_hub/parser_service/updater.py

from ..core.exceptions import ApiRequestError
from ..logging_config import app_logger
from .api_clients import CoinGeckoClient, ExchangeRateApiClient
from .storage import RatesStorage


class RatesUpdater:
    def __init__(self):
        self.storage = RatesStorage()
        self.clients = {
            "coingecko": CoinGeckoClient(),
            "exchangerate": ExchangeRateApiClient()
        }

    def run_update(self, source: str = None) -> int:
        '''
        Запуск обновления курсов
        '''
        app_logger.info("Starting rates update...")
        all_rates = {}
        
        targets = [source] if source else self.clients.keys()
        
        for name in targets:
            if name not in self.clients:
                print(f"Unknown source: {name}")
                continue
                
            client = self.clients[name]
            try:
                rates = client.fetch_rates()
                count = len(rates)
                app_logger.info(f"Fetching from {name}... OK ({count} rates)")
                all_rates.update(rates)
            except ApiRequestError as e:
                app_logger.error(f"Failed to fetch from {name}: {e}")
                print(f"Ошибка при обновлении {name}: {e}")
            except Exception as e:
                app_logger.error(f"Unexpected error in {name}: {e}")

        if all_rates:
            self.storage.save_snapshot(all_rates)
            self.storage.append_history(all_rates)
            
            app_logger.info(f"Writing {len(all_rates)} rates to storage...")
            return len(all_rates)
        
        return 0