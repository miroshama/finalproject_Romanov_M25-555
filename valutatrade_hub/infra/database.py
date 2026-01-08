# valutatrade_hub/infra/database.py

import json
import os
from typing import Any

from .settings import settings


class DatabaseManager:
    '''
    singleton для управления доступом к json-файлам
    '''
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance

    def _get_full_path(self, filename: str) -> str:
        data_dir = settings.get('data_directory', 'data')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        return os.path.join(data_dir, filename)

    def load(self, filename: str) -> Any:
        path = self._get_full_path(filename)
        if not os.path.exists(path):
            return [] if "rates" not in filename else {}
        
        with open(path, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return [] if "rates" not in filename else {}

    def save(self, filename: str, data: Any):
        path = self._get_full_path(filename)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, default=str)

db_manager = DatabaseManager()