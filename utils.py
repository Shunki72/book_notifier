from functools import wraps
from time import sleep


def retry(
        n_retry: int = 10,
        interval: float = 5,
        exceptions: tuple = (Exception,)
    ):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(n_retry):
                try:
                    return func(*args, **kwargs)

                except exceptions:
                    if attempt == n_retry:
                        raise

                    if interval > 0:
                        sleep(interval)

        return wrapper

    return decorator