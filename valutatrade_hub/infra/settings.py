# valutatrade_hub/infra/settings.py

import os
from typing import Any, Dict

try:
    import tomllib
except ImportError:
    tomllib = None


class SettingsLoader:
    '''
    Singleton для загрузки и управления настройками приложения.
    Используется __new__ для гарантии существования только одного экземпляра в памяти.
    '''
    _instance = None
    _settings: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SettingsLoader, cls).__new__(cls)
            cls._instance._load_settings()
        return cls._instance
    
    def _load_settings(self):
        '''
        Загрузка настроек из различных источников:
        1. Значения по умолчанию
        2. Файл pyproject.toml (секция [tool.valutatrade])
        3. Переменные окружения (имеют высший приоритет)
        '''
        default_settings = {
            'data_directory': 'data',
            'rates_ttl_seconds': 300,
            'default_base_currency': 'USD',
            'log_level': 'INFO',
            'log_file': 'logs/valutatrade.log',
            'supported_currencies': ['USD', 'EUR', 'GBP', 'RUB', 'BTC', 'ETH', 'SOL'],
            'api_timeout': 10
        }
        
        self._settings.update(default_settings)
        
        try:
            pyproject_path = 'pyproject.toml'
            if os.path.exists(pyproject_path) and tomllib:
                with open(pyproject_path, 'rb') as f:
                    config_data = tomllib.load(f)
                    valuta_cfg = config_data.get('tool', {}).get('valutatrade', {})
                    if valuta_cfg:
                        self._settings.update(valuta_cfg)
        except Exception:
            pass
        
        env_mapping = {
            'VALUTATRADE_DATA_DIR': 'data_directory',
            'VALUTATRADE_RATES_TTL': 'rates_ttl_seconds',
            'VALUTATRADE_LOG_LEVEL': 'log_level',
            'VALUTATRADE_BASE_CURRENCY': 'default_base_currency',
        }
        
        for env_var, setting_key in env_mapping.items():
            value = os.getenv(env_var)
            if value:
                if setting_key == 'rates_ttl_seconds':
                    self._settings[setting_key] = int(value)
                else:
                    self._settings[setting_key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        '''
        Получение значения настройки по ключу
        '''
        return self._settings.get(key, default)
    
    def reload(self):
        '''
        Полная перезагрузка настроек из файлов и окружения
        '''
        self._settings.clear()
        self._load_settings()
    
    def __getitem__(self, key: str) -> Any:
        return self.get(key)
    
    def __setitem__(self, key: str, value: Any):
        self._settings[key] = value

settings = SettingsLoader()