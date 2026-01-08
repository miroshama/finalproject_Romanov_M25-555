# valutatrade_hub/core/usecases.py

from ..decorators import log_action
from ..infra.database import db_manager
from ..infra.settings import settings
from .currencies import get_currency
from .exceptions import ApiRequestError, InsufficientFundsError
from .models import Portfolio, User


class SystemCore:
    def __init__(self):
        self.db = db_manager
        self.settings = settings

    @log_action("REGISTER")
    def register_user(self, username, password):
        '''
        Функция для регистрации нового пользователя
        '''
        users_file = self.settings.get('users_file', 'users.json')
        users_data = self.db.load(users_file)
        
        for u in users_data:
            if u['username'] == username:
                raise ValueError(f"Имя пользователя '{username}' уже занято")
        
        new_id = 1
        if users_data:
            new_id = max(u['user_id'] for u in users_data) + 1
            
        new_user = User(user_id=new_id, username=username, password=password)
        
        users_data.append(new_user.to_dict())
        self.db.save(users_file, users_data)
        
        portfolios_file = self.settings.get('portfolio_file', 'portfolios.json')
        portfolios_data = self.db.load(portfolios_file)
        
        new_portfolio = Portfolio(new_id)
        base_currency = self.settings.get('default_base_currency', 'USD')
        
        new_portfolio.add_currency(base_currency) 
        new_portfolio.get_wallet(base_currency).deposit(1000.0)
        
        portfolios_data.append(new_portfolio.to_dict())
        self.db.save(portfolios_file, portfolios_data)
        
        return new_user

    @log_action("LOGIN")
    def login_user(self, username, password):
        '''
        Функция авторизации пользователя
        '''
        users_file = self.settings.get('users_file', 'users.json')
        users_data = self.db.load(users_file)
        user_dict = next((u for u in users_data if u['username'] == username), None)
        
        if not user_dict:
            raise ValueError(f"Пользователь '{username}' не найден")
        
        user = User(**user_dict)
        if user.verify_password(password):
            return user
        else:
            raise ValueError("Неверный пароль")

    def get_portfolio(self, user_id):
        '''
        Функция для просмотра портфолио
        '''
        portfolios_file = self.settings.get('portfolio_file', 'portfolios.json')
        data = self.db.load(portfolios_file)
        p_data = next((p for p in data if p['user_id'] == user_id), None)
        if not p_data:
            return Portfolio(user_id)
        return Portfolio(p_data['user_id'], p_data['wallets'])

    def save_portfolio(self, portfolio: Portfolio):
        '''
        Функция сохранения портфолио
        '''
        portfolios_file = self.settings.get('portfolio_file', 'portfolios.json')
        data = self.db.load(portfolios_file)
        for i, p in enumerate(data):
            if p['user_id'] == portfolio.user_id:
                data[i] = portfolio.to_dict()
                self.db.save(portfolios_file, data)
                return
        data.append(portfolio.to_dict())
        self.db.save(portfolios_file, data)

    def get_rates(self):
        '''
        Функция получения оценок 
        '''
        rates_file = self.settings.get('rates_file', 'rates.json')
        data = self.db.load(rates_file)
        if "pairs" in data:
            return data["pairs"]
        return data

    def get_rate(self, from_curr, to_curr):
        '''
        Функция получения оценки
        '''
        get_currency(from_curr)
        get_currency(to_curr)

        rates = self.get_rates()
        pair = f"{from_curr.upper()}_{to_curr.upper()}"
        
        if pair in rates:
            return rates[pair]['rate'], rates[pair]['updated_at']
        
        reverse_pair = f"{to_curr.upper()}_{from_curr.upper()}"
        if reverse_pair in rates:
            return 1 / rates[reverse_pair]['rate'], rates[reverse_pair]['updated_at']
            
        raise ApiRequestError(f"Курс {pair} не найден в базе данных.")

    @log_action("BUY")
    def buy_currency(self, user: User, currency_code: str, amount: float):
        '''
        Функция для покупки валюты за USD
        '''
        if amount <= 0:
            raise ValueError("Количество должно быть положительным")
        
        currency = get_currency(currency_code)
        target_code = currency.code
        
        base_currency = self.settings.get('default_base_currency', 'USD')
        if target_code == base_currency:
            raise ValueError(f"Нельзя купить {base_currency} за {base_currency}")

        portfolio = self.get_portfolio(user.user_id)
        
        try:
            rate, _ = self.get_rate(target_code, base_currency)
        except ApiRequestError:
             raise ValueError(f"Не удалось получить курс для {target_code} -> {base_currency}")
             
        cost_in_base = amount * rate
        
        base_wallet = portfolio.get_wallet(base_currency)
        if not base_wallet:
             raise ValueError(f"У вас нет кошелька {base_currency} для оплаты")
             
        if base_wallet.balance < cost_in_base:
            raise InsufficientFundsError(base_currency, base_wallet.balance, cost_in_base)

        base_wallet.withdraw(cost_in_base)
        
        if not portfolio.get_wallet(target_code):
            portfolio.add_currency(target_code)
        
        portfolio.get_wallet(target_code).deposit(amount)
        
        self.save_portfolio(portfolio)
        return cost_in_base, rate

    @log_action("SELL")
    def sell_currency(self, user: User, currency_code: str, amount: float):
        '''
        Функция для продажи валюты за USD.
        '''
        if amount <= 0:
            raise ValueError("Количество должно быть положительным")
        
        currency = get_currency(currency_code)
        target_code = currency.code
        
        base_currency = self.settings.get('default_base_currency', 'USD')
        if target_code == base_currency:
            raise ValueError(f"Нельзя продать {base_currency}")

        portfolio = self.get_portfolio(user.user_id)
        target_wallet = portfolio.get_wallet(target_code)
        
        if not target_wallet or target_wallet.balance < amount:
            available = target_wallet.balance if target_wallet else 0.0
            raise InsufficientFundsError(target_code, available, amount)
            
        try:
            rate, _ = self.get_rate(target_code, base_currency)
        except ApiRequestError:
             raise ValueError(f"Не удалось получить курс для {target_code} -> {base_currency}")
        
        revenue_in_base = amount * rate
        
        target_wallet.withdraw(amount)
        
        base_wallet = portfolio.get_wallet(base_currency)
        if not base_wallet:
            portfolio.add_currency(base_currency)
            base_wallet = portfolio.get_wallet(base_currency)
            
        base_wallet.deposit(revenue_in_base)
        
        self.save_portfolio(portfolio)
        return revenue_in_base, rate