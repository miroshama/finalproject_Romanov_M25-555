# valutatrade_hub/cli/interface.py

import shlex
from ..core.usecases import SystemCore

class CLI:
    def __init__(self):
        self.core = SystemCore()
        self.current_user = None

    def run(self):
        '''
        Функция для запуска интерфейса
        '''
        print("=== ValutaTrade Hub v1.0 ===")
        print("Доступные команды: register, login, show-portfolio, buy, sell, get-rate, exit, help")
        
        while True:
            try:
                if self.current_user:
                    prompt = f"[{self.current_user.username}]> "
                else:
                    prompt = "> "
                
                command_line = input(prompt).strip()
                if not command_line:
                    continue
                
                parts = shlex.split(command_line)
                command = parts[0].lower()
                args = parts[1:]
                
                if command == 'exit':
                    print("До свидания!")
                    break
                elif command == 'help':
                    self.print_help()
                elif command == 'register':
                    self.handle_register(args)
                elif command == 'login':
                    self.handle_login(args)
                elif command == 'show-portfolio':
                    self.handle_show_portfolio(args)
                elif command == 'buy':
                    self.handle_buy(args)
                elif command == 'sell':
                    self.handle_sell(args)
                elif command == 'get-rate':
                    self.handle_get_rate(args)
                elif command == 'logout':
                    self.current_user = None
                    print("Вы вышли из системы.")
                else:
                    print(f"Неизвестная команда: {command}")
                    
            except KeyboardInterrupt:
                print("\nВыход...")
                break
            except Exception as e:
                print(f"Ошибка: {e}")

    def _parse_args(self, args_list):
        '''
        Функция парсинга строки в словарный вид
        '''
        parsed = {}
        iterator = iter(args_list)
        try:
            for arg in iterator:
                if arg.startswith('--'):
                    key = arg[2:]
                    value = next(iterator)
                    parsed[key] = value
        except StopIteration:
            pass
        return parsed

    def handle_register(self, args):
        '''
        Функция обработки регистрации
        '''
        params = self._parse_args(args)
        if 'username' not in params or 'password' not in params:
            print("Ошибка: укажите --username и --password")
            return
        
        try:
            user = self.core.register_user(params['username'], params['password'])
            print(f"Пользователь '{user.username}' зарегистрирован (id={user.user_id}).")
            print("Бонус 1000 USD начислен! Войдите в систему.")
        except ValueError as e:
            print(str(e))

    def handle_login(self, args):
        '''
        Функция для обработки логина
        '''
        params = self._parse_args(args)
        if 'username' not in params or 'password' not in params:
            print("Ошибка: укажите --username и --password")
            return
            
        try:
            user = self.core.login_user(params['username'], params['password'])
            self.current_user = user
            print(f"Вы вошли как '{user.username}'")
        except ValueError as e:
            print(str(e))

    def handle_show_portfolio(self, args):
        '''
        Функция обработки показа портфолио
        '''
        if not self.current_user:
            print("Сначала выполните login")
            return
            
        params = self._parse_args(args)
        base = params.get('base', 'USD')
        
        portfolio = self.core.get_portfolio(self.current_user.user_id)
        rates = self.core.get_rates()
        
        print(f"Портфель пользователя '{self.current_user.username}' (база: {base}):")
        
        total_val = portfolio.get_total_value(base, rates)
        wallets = portfolio.wallets
        
        if not wallets:
            print("Портфель пуст.")
        
        for code, wallet in wallets.items():
            val_in_base = 0
            if code == base:
                val_in_base = wallet.balance
            else:
                pair = f"{code}_{base}"
                if pair in rates:
                    val_in_base = wallet.balance * rates[pair]['rate']
            
            print(f"- {code}: {wallet.balance:.4f} \t-> {val_in_base:.2f} {base}")
            
        print("-" * 30)
        print(f"ИТОГО: {total_val:.2f} {base}")

    def handle_buy(self, args):
        '''
        Функция обработки покупки
        '''
        if not self.current_user:
            print("Сначала выполните login")
            return

        params = self._parse_args(args)
        if 'currency' not in params or 'amount' not in params:
            print("Использование: buy --currency <CODE> --amount <NUM>")
            return

        try:
            currency = params['currency']
            amount = float(params['amount'])
            
            cost, rate = self.core.buy_currency(self.current_user, currency, amount)
            print(f"Покупка выполнена: {amount} {currency} по курсу {rate} USD.")
            print(f"Списано: {cost:.2f} USD")
            
        except ValueError as e:
            print(f"Ошибка транзакции: {e}")

    def handle_sell(self, args):
        '''
        Функция обработки продажи
        '''
        if not self.current_user:
            print("Сначала выполните login")
            return

        params = self._parse_args(args)
        if 'currency' not in params or 'amount' not in params:
            print("Использование: sell --currency <CODE> --amount <NUM>")
            return

        try:
            currency = params['currency']
            amount = float(params['amount'])
            
            revenue, rate = self.core.sell_currency(self.current_user, currency, amount)
            print(f"Продажа выполнена: {amount} {currency} по курсу {rate} USD.")
            print(f"Получено: {revenue:.2f} USD")
            
        except ValueError as e:
            print(f"Ошибка транзакции: {e}")

    def handle_get_rate(self, args):
        '''
        Функция обработки показа оценки
        '''
        params = self._parse_args(args)
        if 'from' not in params or 'to' not in params:
            print("Использование: get-rate --from <CODE> --to <CODE>")
            return
            
        try:
            val, updated = self.core.get_rate(params['from'], params['to'])
            print(f"Курс {params['from'].upper()} -> {params['to'].upper()}: {val}")
            print(f"(Обновлено: {updated})")
        except ValueError as e:
            print(e)

    def print_help(self):
        '''
        Функция вывода справочной информации
        '''
        print("""
        Команды:
        register --username <name> --password <pass>
        login --username <name> --password <pass>
        logout
        show-portfolio [--base <USD|EUR|...>]
        buy --currency <CODE> --amount <float> (покупка за USD)
        sell --currency <CODE> --amount <float> (продажа за USD)
        get-rate --from <CODE> --to <CODE>
        exit
        """)