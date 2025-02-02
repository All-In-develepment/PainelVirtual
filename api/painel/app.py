import logging
from logging.handlers import SMTPHandler
from werkzeug.middleware.proxy_fix import ProxyFix

import stripe

from flask import Flask, render_template
from flask_login import LoginManager
from celery import Celery
from itsdangerous import URLSafeTimedSerializer

from painel.blueprints.admin import admin
from painel.blueprints.kirongames import kirongames
from painel.blueprints.page import page
from painel.blueprints.contact import contact
from painel.blueprints.user import user
from painel.blueprints.billing import billing
from painel.blueprints.billing import stripe_webhook
from painel.blueprints.user.models import User
from painel.blueprints.billing.template_processors import (format_currency, current_year)
from painel.extensions import debug_toolbar, mail, csrf, db, login_manager

CELERY_TASK_LIST = [
    'painel.blueprints.contact.tasks',
    'painel.blueprints.user.tasks',
    'painel.blueprints.billing.tasks'
]

def create_celery_app(app=None):
    """
    Create a new Celery object and tie together the Celery config to the app's
    config. Wrap all tasks in the context of the application.

    :param app: Flask app
    :return: Celery app
    """
    app = app or create_app()

    celery = Celery(app.import_name,
                    broker=app.config['CELERY_BROKER_URL'],
                    include=CELERY_TASK_LIST)
    celery.conf.update(app.config)

    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery

def create_app(settings_override=None):
    """
    Create a Flask application using the app factory pattern.

    :param settings_override: Override settings
    :return: Flask app
    """
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_object('config.settings')
    app.config.from_pyfile('settings.py', silent=True)

    if settings_override:
        app.config.update(settings_override)
        
    stripe.api_key = app.config.get('STRIPE_SECRET_KEY')
    stripe.api_version = app.config.get('STRIPE_API_VERSION')

    middleware(app)
    error_templates(app)
    exception_handler(app)
    app.register_blueprint(admin)
    app.register_blueprint(page)
    app.register_blueprint(contact)
    app.register_blueprint(user)
    app.register_blueprint(billing)
    app.register_blueprint(stripe_webhook)
    app.register_blueprint(kirongames)
    template_processors(app)
    extensions(app)
    authentication(app, User)

    return app

def authentication(app, user_model):
    """
    Initialize the Flask-Login extension (mutates the app passed in).

    :param app: Flask application instance
    :param user_model: Model that contains the authentication information
    :type user_model: SQLAlchemy model
    :return: None
    """
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'user.login'

    @login_manager.user_loader
    def load_user(uid):
        return user_model.query.get(uid)
    
    # @login_manager.token_loader
    # def load_token(token):
    #     duration = app.config['REMEMBER_COOKIE_DURATION'].total_seconds()
    #     serializer = URLSafeTimedSerializer(app.secret_key)

    #     data = serializer.loads(token, max_age=duration)
    #     user_uid = data[0]

    #     return user_model.query.get(user_uid)
    return None

def generate_token(user, app):
    """Gera um token para lembrar o usuário."""
    serializer = URLSafeTimedSerializer(app.secret_key)
    return serializer.dumps([str(user.id)])

def verify_token(token, app):
    """Verifica e carrega um usuário a partir do token."""
    serializer = URLSafeTimedSerializer(app.secret_key)
    try:
        data = serializer.loads(token, max_age=app.config['REMEMBER_COOKIE_DURATION'].total_seconds())
        return User.query.get(data[0])
    except Exception:
        return None

def template_processors(app):
    """
    Register 0 or more custom template processors (mutates the app passed in).

    :param app: Flask application instance
    :return: App jinja environment
    """
    app.jinja_env.filters['format_currency'] = format_currency
    app.jinja_env.globals.update(current_year=current_year)

    # Configuração do Jinja para controlar o espaçamento
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True
    
    return app.jinja_env

def extensions(app):
    """
    Register 0 or more extensions (mutates the app passed in).

    :param app: Flask application instance
    :return: None
    """
    debug_toolbar.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)

    return None

def middleware(app):
    """
    Register 0 or more middleware (mutates the app passed in).

    :param app: Flask application instance
    :return: None
    """
    # Swap request.remote_addr with the real IP address even if behind a proxy.
    app.wsgi_app = ProxyFix(app.wsgi_app)

    return None

def error_templates(app):
    """
    Register 0 or more custom error pages (mutates the app passed in).

    :param app: Flask application instance
    :return: None
    """

    def render_status(status):
        """
        Render a custom template for a specific status.
            Source: http://stackoverflow.com/a/30108946

        :param status: Status as a written name
        :type status: str
        :return: None
        """
        # Get the status code from the status, default to a 500 so that we
        # catch all types of errors and treat them as a 500.
        code = getattr(status, 'code', 500)
        return render_template('errors/{0}.html'.format(code)), code

    for error in [404, 500]:
        app.errorhandler(error)(render_status)

    return None

def exception_handler(app):
    """
    Register 0 or more exception handlers (mutates the app passed in).

    :param app: Flask application instance
    :return: None
    """
    mail_handler = SMTPHandler((app.config.get('MAIL_SERVER'),
                                app.config.get('MAIL_PORT')),
                                app.config.get('MAIL_USERNAME'),
                                [app.config.get('MAIL_USERNAME')],
                                '[Exception handler] A 5xx was thrown',
                                (app.config.get('MAIL_USERNAME'),
                                app.config.get('MAIL_PASSWORD')),
                                secure=())

    mail_handler.setLevel(logging.ERROR)
    mail_handler.setFormatter(logging.Formatter("""
    Time:               %(asctime)s
    Message type:       %(levelname)s


    Message:

    %(message)s
    """))
    app.logger.addHandler(mail_handler)

    return None
