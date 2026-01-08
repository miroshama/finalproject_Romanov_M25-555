# valutatrade_hub/decorators.py

import functools

from .logging_config import app_logger


def log_action(action_name):
    '''
    Декоратор логирования бизнес-операций
    '''
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            user_id = args[1] if len(args) > 1 else "unknown"
            
            try:
                result = func(*args, **kwargs)
                app_logger.info(
                    f"{action_name} user_id={user_id} args={args[2:]} kwargs={kwargs} result=OK"
                )
                return result
            except Exception as e:
                app_logger.error(
                    f"{action_name} user_id={user_id} result=ERROR type={type(e).__name__} msg='{str(e)}'"
                )
                raise e
        return wrapper
    return decorator