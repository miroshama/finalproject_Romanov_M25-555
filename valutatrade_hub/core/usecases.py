# valutatrade_hub/core/usecases.py

from .models import User, Portfolio
from .utils import load_json, save_json

USERS_FILE = 'users.json'
PORTFOLIOS_FILE = 'portfolios.json'
RATES_FILE = 'rates.json'

class SystemCore:
    def __init__(self):
        pass

    def register_user(self, username, password):
        '''
        Функция для регистрации нового пользователя
        '''
        users_data = load_json(USERS_FILE)
        
        for u in users_data:
            if u['username'] == username:
                raise ValueError(f"Имя пользователя '{username}' уже занято")
        
        new_id = 1
        if users_data:
            new_id = max(u['user_id'] for u in users_data) + 1
            
        new_user = User(user_id=new_id, username=username, password=password)
        
        users_data.append(new_user.to_dict())
        save_json(USERS_FILE, users_data)
        
        portfolios_data = load_json(PORTFOLIOS_FILE)
        new_portfolio = Portfolio(new_id)
        new_portfolio.add_currency("USD") 
        new_portfolio.get_wallet("USD").deposit(1000.0)
        
        portfolios_data.append(new_portfolio.to_dict())
        save_json(PORTFOLIOS_FILE, portfolios_data)
        
        return new_user

    def login_user(self, username, password):
        '''
        Функция авторизации пользователя
        '''
        users_data = load_json(USERS_FILE)
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
        data = load_json(PORTFOLIOS_FILE)
        p_data = next((p for p in data if p['user_id'] == user_id), None)
        if not p_data:
            return Portfolio(user_id)
        return Portfolio(p_data['user_id'], p_data['wallets'])

    def save_portfolio(self, portfolio: Portfolio):
        '''
        Функция сохранения портфолио
        '''
        data = load_json(PORTFOLIOS_FILE)
        for i, p in enumerate(data):
            if p['user_id'] == portfolio.user_id:
                data[i] = portfolio.to_dict()
                save_json(PORTFOLIOS_FILE, data)
                return
        data.append(portfolio.to_dict())
        save_json(PORTFOLIOS_FILE, data)

    def get_rates(self):
        '''
        Функция получения оценок 
        '''
        return load_json(RATES_FILE)

    def get_rate(self, from_curr, to_curr):
        '''
        Функция получения оценки
        '''
        rates = self.get_rates()
        pair = f"{from_curr.upper()}_{to_curr.upper()}"
        
        if pair in rates:
            return rates[pair]['rate'], rates[pair]['updated_at']
        
        reverse_pair = f"{to_curr.upper()}_{from_curr.upper()}"
        if reverse_pair in rates:
            return 1 / rates[reverse_pair]['rate'], rates[reverse_pair]['updated_at']
            
        raise ValueError(f"Курс {pair} не найден.")

    def buy_currency(self, user: User, currency_code: str, amount: float):
        '''
        Функция для покупки валюты за USD
        '''
        if amount <= 0:
            raise ValueError("Количество должно быть положительным")
        
        currency_code = currency_code.upper()
        if currency_code == "USD":
            raise ValueError("Нельзя купить USD за USD")

        portfolio = self.get_portfolio(user.user_id)
        rates = self.get_rates()
        
        pair = f"{currency_code}_USD"
        if pair not in rates:
             raise ValueError(f"Не удалось получить курс для {currency_code} -> USD")
             
        rate = rates[pair]['rate']
        cost_in_usd = amount * rate
        
        usd_wallet = portfolio.get_wallet("USD")
        if not usd_wallet:
             raise ValueError("У вас нет кошелька USD для оплаты")
             
        usd_wallet.withdraw(cost_in_usd)
        
        if not portfolio.get_wallet(currency_code):
            portfolio.add_currency(currency_code)
        
        portfolio.get_wallet(currency_code).deposit(amount)
        
        self.save_portfolio(portfolio)
        return cost_in_usd, rate

    def sell_currency(self, user: User, currency_code: str, amount: float):
        '''
        Функция для продажи валюты за USD.
        '''
        if amount <= 0:
            raise ValueError("Количество должно быть положительным")
        
        currency_code = currency_code.upper()
        if currency_code == "USD":
            raise ValueError("Нельзя продать USD")

        portfolio = self.get_portfolio(user.user_id)
        target_wallet = portfolio.get_wallet(currency_code)
        
        if not target_wallet:
            raise ValueError(f"У вас нет кошелька {currency_code}")
            
        rates = self.get_rates()
        pair = f"{currency_code}_USD"
        
        if pair not in rates:
             raise ValueError(f"Не удалось получить курс для {currency_code} -> USD")
        
        rate = rates[pair]['rate']
        revenue_in_usd = amount * rate
        
        target_wallet.withdraw(amount)
        
        usd_wallet = portfolio.get_wallet("USD")
        if not usd_wallet:
            portfolio.add_currency("USD")
            usd_wallet = portfolio.get_wallet("USD")
            
        usd_wallet.deposit(revenue_in_usd)
        
        self.save_portfolio(portfolio)
        return revenue_in_usd, rate