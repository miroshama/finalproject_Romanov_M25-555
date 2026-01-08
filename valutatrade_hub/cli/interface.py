# valutatrade_hub/cli/interface.py

import shlex

from ..core.currencies import _CURRENCY_REGISTRY as CURRENCY_REGISTRY
from ..core.exceptions import ApiRequestError, CurrencyNotFoundError, InsufficientFundsError
from ..core.usecases import SystemCore
from ..infra.database import db_manager
from ..parser_service.config import parser_config
from ..parser_service.updater import RatesUpdater


class CLI:
    '''
    Класс реализации интерфейса
    '''
    def __init__(self):
        self.core = SystemCore()
        self.current_user = None

    def run(self):
        print("=== ValutaTrade Hub v2.1 ===")
        print("Команды: register, login, show-portfolio, buy, sell, get-rate, update-rates, show-rates, exit, help")
        
        while True:
            try:
                if self.current_user:
                    prompt = f"[{self.current_user.username}]> "
                else:
                    prompt = "> "
                
                try:
                    command_line = input(prompt).strip()
                except EOFError:
                    print("\nВыход...")
                    break
                
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
                elif command == 'update-rates':
                    self.handle_update_rates(args)
                elif command == 'show-rates':
                    self.handle_show_rates(args)
                elif command == 'logout':
                    self.current_user = None
                    print("Вы вышли из системы.")
                else:
                    print(f"Неизвестная команда: {command}")
                    
            except KeyboardInterrupt:
                print("\nВыход...")
                break
            except Exception as e:
                print(f"Критическая ошибка: {e}")

    def _parse_args(self, args_list):
        parsed = {}
        iterator = iter(args_list)
        try:
            for arg in iterator:
                if arg.startswith('--'):
                    key = arg[2:]
                    try:
                        value = next(iterator)
                        parsed[key] = value
                    except StopIteration:
                        print(f"Ошибка: аргумент --{key} требует значения")
                        return None
        except StopIteration:
            pass
        return parsed

    def handle_register(self, args):
        '''
        Обработка регистрации нового пользователя
        '''
        params = self._parse_args(args)
        if not params or 'username' not in params or 'password' not in params:
            print("Ошибка: укажите --username и --password")
            return
        
        try:
            user = self.core.register_user(params['username'], params['password'])
            print(f"Пользователь '{user.username}' успешно зарегистрирован (id={user.user_id}).")
            print("Бонус 1000 USD начислен! Теперь выполните вход (login).")
        except ValueError as e:
            print(f"Ошибка регистрации: {e}")
        except Exception as e:
            print(f"Ошибка: {e}")

    def handle_login(self, args):
        '''
        Обработка авторизации
        '''
        params = self._parse_args(args)
        if not params or 'username' not in params or 'password' not in params:
            print("Ошибка: укажите --username и --password")
            return
            
        try:
            user = self.core.login_user(params['username'], params['password'])
            self.current_user = user
            print(f"Добро пожаловать, {user.username}!")
        except ValueError as e:
            print(f"Ошибка входа: {e}")

    def handle_show_portfolio(self, args):
        '''
        Обработка показа портфолио
        '''
        if not self.current_user:
            print("Сначала выполните login")
            return
            
        params = self._parse_args(args) or {}
        base = params.get('base', self.core.settings.get('default_base_currency', 'USD'))
        
        try:
            portfolio = self.core.get_portfolio(self.current_user.user_id)
            rates_data = self.core.get_rates()
            
            print(f"\nПортфель пользователя '{self.current_user.username}' (оценка в {base}):")
            print("-" * 50)
            
            total_val = 0.0
            wallets = portfolio.wallets
            
            if not wallets:
                print("Портфель пуст.")
            
            for code, wallet in wallets.items():
                val_in_base = 0.0
                if code == base:
                    val_in_base = wallet.balance
                else:
                    pair = f"{code}_{base}"
                    rev_pair = f"{base}_{code}"
                    
                    if pair in rates_data:
                        val_in_base = wallet.balance * rates_data[pair]['rate']
                    elif rev_pair in rates_data:
                        val_in_base = wallet.balance * (1 / rates_data[rev_pair]['rate'])
                
                total_val += val_in_base
                print(f"- {code:<5}: {wallet.balance:>12.4f}  -> {val_in_base:>12.2f} {base}")
                
            print("-" * 50)
            print(f"ИТОГО : {total_val:>12.2f} {base}\n")
            
        except Exception as e:
            print(f"Ошибка при отображении портфеля: {e}")

    def handle_buy(self, args):
        '''
        Обработка покупки
        '''
        if not self.current_user:
            print("Сначала выполните login")
            return

        params = self._parse_args(args)
        if not params or 'currency' not in params or 'amount' not in params:
            print("Использование: buy --currency <CODE> --amount <NUM>")
            return

        try:
            currency = params['currency']
            amount = float(params['amount'])
            
            cost, rate = self.core.buy_currency(self.current_user, currency, amount)
            
            base = self.core.settings.get('default_base_currency', 'USD')
            print(f"Покупка успешно выполнена: {amount} {currency.upper()}")
            print(f"Курс сделки: {rate} {base}")
            print(f"Списано:     {cost:.2f} {base}")
            
        except ValueError as e:
            print(f"Ошибка валидации: {e}")
        except InsufficientFundsError as e:
            print(f"Ошибка: {e}")
        except CurrencyNotFoundError as e:
            print(f"Ошибка: {e}. Проверьте правильность кода валюты.")
        except ApiRequestError as e:
            print(f"Ошибка API: {e}. Попробуйте позже.")
        except Exception as e:
            print(f"Ошибка транзакции: {e}")

    def handle_sell(self, args):
        '''
        Обработка продажи
        '''
        if not self.current_user:
            print("Сначала выполните login")
            return

        params = self._parse_args(args)
        if not params or 'currency' not in params or 'amount' not in params:
            print("Использование: sell --currency <CODE> --amount <NUM>")
            return

        try:
            currency = params['currency']
            amount = float(params['amount'])
            
            revenue, rate = self.core.sell_currency(self.current_user, currency, amount)
            
            base = self.core.settings.get('default_base_currency', 'USD')
            print(f"Продажа успешно выполнена: {amount} {currency.upper()}")
            print(f"Курс сделки: {rate} {base}")
            print(f"Получено:    {revenue:.2f} {base}")
            
        except ValueError as e:
            print(f"Ошибка валидации: {e}")
        except InsufficientFundsError as e:
            print(f"Ошибка: {e}")
        except CurrencyNotFoundError as e:
            print(f"Ошибка: {e}")
        except ApiRequestError as e:
            print(f"Ошибка API: {e}")
        except Exception as e:
            print(f"Ошибка транзакции: {e}")

    def handle_get_rate(self, args):
        '''
        Обработка получения курсов
        '''
        params = self._parse_args(args)
        if not params or 'from' not in params or 'to' not in params:
            print("Использование: get-rate --from <CODE> --to <CODE>")
            return
            
        try:
            val, updated = self.core.get_rate(params['from'], params['to'])
            print(f"Курс {params['from'].upper()} -> {params['to'].upper()}: {val}")
            print(f"(Обновлено: {updated})")
            
        except CurrencyNotFoundError as e:
            print(f"Ошибка: {e}")
            available = ", ".join(sorted(CURRENCY_REGISTRY.keys()))
            print(f"Доступные валюты: {available}")
            
        except ApiRequestError as e:
            print(f"Ошибка API: {e}")
            print("Возможно, сервис обновлений недоступен или пара не торгуется.")
            
        except Exception as e:
            print(f"Ошибка: {e}")

    def handle_update_rates(self, args):
        '''
        Функция для запуска обновления курсов из API
        '''
        params = self._parse_args(args) or {}
        source = params.get('source')
        
        print("Запуск обновления курсов из внешних источников...")
        updater = RatesUpdater()
        
        try:
            count = updater.run_update(source)
            if count > 0:
                print(f"Обновление завершено. Всего обновлено пар: {count}.")
            else:
                print("Новых данных не получено. Проверьте соединение или API ключи.")
        except Exception as e:
            print(f"Критическая ошибка при обновлении: {e}")

    def handle_show_rates(self, args):
        '''
        Функция для демонстрации актуальных курсов
        '''
        params = self._parse_args(args) or {}
        currency_filter = params.get('currency')
        top_n = int(params.get('top', 0))
        
        raw_data = db_manager.load(parser_config.RATES_FILE)
        
        if isinstance(raw_data, dict) and "pairs" in raw_data:
            rates_data = raw_data["pairs"]
            updated_at = raw_data.get("last_refresh", "Unknown")
        else:
            rates_data = raw_data
            updated_at = "Unknown (Legacy format)"

        if not rates_data:
            print("Локальный кеш курсов пуст. Выполните 'update-rates'.")
            return

        print(f"\nАктуальные курсы из кеша (обновлено: {updated_at}):")
        print("-" * 40)
        
        items = []
        for pair, info in rates_data.items():
            rate_val = info['rate'] if isinstance(info, dict) else info
            items.append((pair, rate_val))

        if currency_filter:
            curr = currency_filter.upper()
            items = [x for x in items if curr in x[0]]
            if not items:
                print(f"Курс для валюты '{curr}' не найден.")
                return

        if top_n > 0:
            items.sort(key=lambda x: x[1], reverse=True)
            items = items[:top_n]
        else:
            items.sort(key=lambda x: x[0])

        for pair, rate in items:
            print(f"{pair:<10}: {rate:>15.6f}")
        print("-" * 40 + "\n")

    def print_help(self):
        print("""
        Доступные команды:
        -----------------
        register --username <name> --password <pass> - Регистрация
        login    --username <name> --password <pass> - Вход
        logout                                       - Выход
        show-portfolio [--base <CODE>]               - Состояние кошелька
        buy      --currency <CODE> --amount <num>    - Купить валюту
        sell     --currency <CODE> --amount <num>    - Продать валюту
        get-rate --from <CODE> --to <CODE>           - Получить курс пары
        update-rates [--source <name>]               - Обновить курсы из API
        show-rates   [--currency <CODE>] [--top <N>] - Показать кеш курсов
        exit                                         - Завершить работу
        help                                         - Показать это сообщение
        """)