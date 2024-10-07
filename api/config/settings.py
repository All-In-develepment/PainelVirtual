from datetime import timedelta
from celery.schedules import crontab

DEBUG = True
LOG_LEVEL = 'DEBUG'  # CRITICAL / ERROR / WARNING / INFO / DEBUG
SERVER_NAME = 'localhost:8000'
SECRET_KEY = 'secret'

# FLASK-MAIL
MAIL_DEFAULT_SENDER = 'ronaldo@grupoall.in'
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USE_SSL = False
MAIL_USERNAME = 'ronaldo@grupoall.in'
MAIL_PASSWORD = 'ygwp fdeg cerk bbtu'

# CELERY
CELERY_BROKER_URL = 'redis://:devpassword@redis:6379/0'
CELERY_RESULT_BACKEND = 'redis://:devpassword@redis:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_REDIS_MAX_CONNECTIONS = 5
CELERYBEAT_SCHEDULE = {
    'mark-soon-to-expire-credit-cards': {
        'task': 'snakeeyes.blueprints.billing.tasks.mark_old_credit_cards',
        'schedule': crontab(hour=0, minute=0)
    },
    'expire-old-coupons': {
        'task': 'snakeeyes.blueprints.billing.tasks.expire_old_coupons',
        'schedule': crontab(hour=0, minute=1)
    },
}

# SQLAlchemy.
db_uri = 'postgresql://snakeeyes:devpassword@postgres:5432/snakeeyes'
SQLALCHEMY_DATABASE_URI = db_uri
SQLALCHEMY_TRACK_MODIFICATIONS = False

# User.
SEED_ADMIN_EMAIL = 'dev@local.host'
SEED_ADMIN_PASSWORD = 'devpassword'
REMEMBER_COOKIE_DURATION = timedelta(days=90)

# Billing.
STRIPE_SECRET_KEY = None
STRIPE_PUBLISHABLE_KEY = None
STRIPE_API_VERSION = '2024-06-20'
STRIPE_PLANS = {
    '0': {
        'id': 'bronze-mensal',
        'name': 'Bronze',
        'amount': 100,
        'currency': 'brl',
        'interval': 'month',
        'interval_count': 1,
        'trial_period_days': 14,
        # 'statement_descriptor': 'SNAKEEYES BRONZE',
        'metadata': {},
        'product': 'bronze'
    },
    '1': {
        'id': 'gold-mensal',
        'name': 'Gold',
        'amount': 500,
        'currency': 'brl',
        'interval': 'month',
        'interval_count': 1,
        'trial_period_days': 14,
        # 'statement_descriptor': 'SNAKEEYES GOLD',
        'metadata': {
            'recommended': True
        },
        'product': 'gold'
    },
    '2': {
        'id': 'platinum-mensal',
        'name': 'Platinum',
        'amount': 1000,
        'currency': 'brl',
        'interval': 'month',
        'interval_count': 1,
        'trial_period_days': 14,
        # 'statement_descriptor': 'SNAKEEYES PLATINUM',
        'metadata': {},
        'product': 'platinum'
    }
}

STRIPE_PRODUCTS = {
    '0': {
        'id': 'bronze',
        'name': 'Bronze',
        'type': 'service',
        'metadata': {}
    },
    '1': {
        'id': 'gold',
        'name': 'Gold',
        'type': 'service',
        'metadata': {
            'recommended': True
        }
    },
    '2': {
        'id': 'platinum',
        'name': 'Platinum',
        'type': 'service',
        'metadata': {}
    }
}
