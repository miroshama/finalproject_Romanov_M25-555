# valutatrade_hub/core/models.py

import uuid
import datetime
from .utils import hash_password

class User:
    '''
    Класс "пользователь системы"
    '''
    def __init__(self, user_id, username, password=None, hashed_password=None, salt=None, registration_date=None):
        self._user_id = user_id
        self._username = username
        
        if password and not hashed_password:
            self._salt = uuid.uuid4().hex
            self.password = password 

        else:
            self._hashed_password = hashed_password
            self._salt = salt
        
        if registration_date:
             if isinstance(registration_date, str):
                self._registration_date = datetime.datetime.fromisoformat(registration_date)
             else:
                self._registration_date = registration_date
        else:
            self._registration_date = datetime.datetime.now()

    @property
    def user_id(self):
        return self._user_id

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, value):
        if not value:
            raise ValueError("Имя пользователя не может быть пустым")
        self._username = value

    @property
    def salt(self):
        return self._salt

    @property
    def hashed_password(self):
        return self._hashed_password
    
    @property
    def registration_date(self):
        return self._registration_date

    @property
    def password(self):
        return self._hashed_password 

    @password.setter
    def password(self, raw_password):
        if len(raw_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")
        self._hashed_password = hash_password(raw_password, self._salt)

    def get_user_info(self):
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date.isoformat()
        }

    def change_password(self, new_password):
        self.password = new_password

    def verify_password(self, password):
        check_hash = hash_password(password, self._salt)
        return check_hash == self._hashed_password
    
    def to_dict(self):
        return {
            "user_id": self._user_id,
            "username": self._username,
            "hashed_password": self._hashed_password,
            "salt": self._salt,
            "registration_date": self._registration_date.isoformat()
        }


class Wallet:
    '''
    Класс "Кошелёк пользователя для одной конкретной валюты"
    '''
    def __init__(self, currency_code: str, balance: float = 0.0):
        self.currency_code = currency_code.upper()
        self._balance = float(balance)

    @property
    def balance(self):
        return self._balance

    @balance.setter
    def balance(self, value):
        if not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")
        self._balance = float(value)

    def deposit(self, amount: float):
        if amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительной")
        self.balance += amount

    def withdraw(self, amount: float):
        if amount <= 0:
            raise ValueError("Сумма снятия должна быть положительной")
        if amount > self._balance:
            raise ValueError(f"Недостаточно средств. Доступно: {self._balance}")
        self.balance -= amount

    def get_balance_info(self):
        return f"{self.currency_code}: {self._balance:.4f}"
    
    def to_dict(self):
        return {"currency_code": self.currency_code, "balance": self._balance}


class Portfolio:
    '''
    Класс "Управление всеми кошельками одного пользователя"
    '''
    def __init__(self, user_id: int, wallets_data: dict = None):
        self._user_id = user_id
        self._wallets = {}
        
        if wallets_data:
            for code, data in wallets_data.items():
                self._wallets[code] = Wallet(data['currency_code'], data['balance'])

    @property
    def user_id(self):
        return self._user_id

    @property
    def wallets(self):
        return self._wallets.copy()

    def get_wallet(self, currency_code: str) -> Wallet:
        return self._wallets.get(currency_code.upper())

    def add_currency(self, currency_code: str):
        code = currency_code.upper()
        if code in self._wallets:
            raise ValueError(f"Кошелек {code} уже существует")
        self._wallets[code] = Wallet(code, 0.0)

    def get_total_value(self, base_currency='USD', rates_data=None):
        '''
        Функция для суммирования.
        '''
        total = 0.0
        base = base_currency.upper()
        
        for wallet in self._wallets.values():
            if wallet.currency_code == base:
                total += wallet.balance
                continue
            
            pair = f"{wallet.currency_code}_{base}"
            
            rate = 0.0
            if rates_data and pair in rates_data:
                rate = rates_data[pair]['rate']
            elif rates_data and f"{base}_{wallet.currency_code}" in rates_data:
                rate = 1 / rates_data[f"{base}_{wallet.currency_code}"]['rate']
            
            total += wallet.balance * rate
            
        return total

    def to_dict(self):
        return {
            "user_id": self._user_id,
            "wallets": {code: w.to_dict() for code, w in self._wallets.items()}
        }