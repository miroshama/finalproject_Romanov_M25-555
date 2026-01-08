# valutatrade_hub/core/utils.py

import hashlib
import json
import os
from datetime import datetime

DATA_DIR = os.path.join(os.getcwd(), 'data')

def ensure_data_files():
    '''
    Функция для создания папки data и json файлов, в случае, если они отсутствуют 
    '''
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    files = {
        'users.json': [],
        'portfolios.json': [],
        'rates.json': {
            "BTC_USD": {"rate": 59337.21, "updated_at": datetime.now().isoformat()},
            "EUR_USD": {"rate": 1.0786, "updated_at": datetime.now().isoformat()},
            "USD_USD": {"rate": 1.0, "updated_at": datetime.now().isoformat()}
        }
    }

    for filename, default_content in files.items():
        path = os.path.join(DATA_DIR, filename)
        if not os.path.exists(path):
            save_json(filename, default_content)

def load_json(filename):
    '''
    Функция для загрузки json файла
    
    Переменная filename: Имя файла
    '''
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return [] if filename != 'rates.json' else {}
    with open(path, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return [] if filename != 'rates.json' else {}

def save_json(filename, data):
    '''
    Функция для сохранения данных в json
    
    Переменная filename: название json файла
    Переменная data: Данные для записи в json
    '''
    path = os.path.join(DATA_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, default=str)

def hash_password(password: str, salt: str) -> str:
    '''
    Функция хэширования пользовательского пароля
    '''
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()