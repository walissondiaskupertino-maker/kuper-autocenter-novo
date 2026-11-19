import os
import secrets
from datetime import timedelta
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

class Config:
    APP_ENV = os.getenv('APP_ENV', 'development').lower()
    DEBUG = APP_ENV == 'development'
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        if APP_ENV == 'production':
            raise RuntimeError("A variável de ambiente SECRET_KEY não foi configurada.")
        SECRET_KEY = secrets.token_hex(32)

    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '3306')
    DB_NAME = os.getenv('DB_NAME', 'kuper_autocenter')
    DATABASE_URL = os.getenv('DATABASE_URL')

    if bool(DB_USER) != bool(DB_PASSWORD):
        raise RuntimeError(
            "Configure DB_USER e DB_PASSWORD juntos ou use DATABASE_URL."
        )

    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    elif DB_USER and DB_PASSWORD:
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASSWORD)}@"
            f"{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )
    elif APP_ENV == 'production':
        raise RuntimeError(
            "Configure DATABASE_URL ou DB_USER e DB_PASSWORD em produção."
        )
    else:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///kuper_autocenter.db'

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 280,
    }
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = APP_ENV == 'production'
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_SECURE = APP_ENV == 'production'
    REMEMBER_COOKIE_DURATION = timedelta(days=14)
