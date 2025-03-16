from flask import (
    g, redirect, url_for
)

import logging
from functools import wraps

logging.basicConfig(level=logging.INFO)


# Exception handler
def exception_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.exception(f"Exception occurred in {func.__name__}")
    return wrapper

# Global authentication checker
def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None: return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view