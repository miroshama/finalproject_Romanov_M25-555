# valutatrade_hub/parser_service/storage.py

from datetime import datetime

from ..infra.database import db_manager
from .config import parser_config


class RatesStorage:
    def __init__(self):
        self.db = db_manager

    def save_snapshot(self, new_rates: dict):
        '''
        Функция обновления текущих курсов
        '''
        current_data = self.db.load(parser_config.RATES_FILE)
        
        if "pairs" not in current_data:
            current_data = {"pairs": {}, "last_refresh": None}
            
        current_data["pairs"].update(new_rates)
        current_data["last_refresh"] = datetime.utcnow().isoformat()
        
        self.db.save(parser_config.RATES_FILE, current_data)

    def append_history(self, new_rates: dict):
        '''
        Функция добавления истории курсов в exchange_rates.json
        '''
        history = self.db.load(parser_config.HISTORY_FILE)
        if not isinstance(history, list):
            history = []

        for pair, info in new_rates.items():

            parts = pair.split('_')
            from_curr, to_curr = parts[0], parts[1]
            
            record = {
                "id": f"{pair}_{info['updated_at']}",
                "from_currency": from_curr,
                "to_currency": to_curr,
                "rate": info['rate'],
                "timestamp": info['updated_at'],
                "source": info['source']
            }
            history.append(record)
        
        self.db.save(parser_config.HISTORY_FILE, history)