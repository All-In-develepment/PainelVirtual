import click
import random

from datetime import datetime

from faker import Faker

from painel.app import create_app
from painel.extensions import db
from painel.blueprints.user.models import User
from painel.blueprints.billing.models.invoice import Invoice

# Create an app context for the database connection.
app = create_app()
db.app = app

fake = Faker()


def _log_status(count, model_label):
    """
    Log the output of how many records were created.

    :param count: Amount created
    :type count: int
    :param model_label: Name of the model
    :type model_label: str
    :return: None
    """
    click.echo('Created {0} {1}'.format(count, model_label))

    return None


def _bulk_insert(model, data, label):
    """
    Bulk insert data to a specific model and log it. This is much more
    efficient than adding 1 row at a time in a loop.

    :param model: Model being affected
    :type model: SQLAlchemy
    :param data: Data to be saved
    :type data: list
    :param label: Label for the output
    :type label: str
    :return: None
    """
    with app.app_context():
        # try:
        # Inicia uma transação
        # with db.session.begin():
        
        # Remove todos os registros da tabela
        model.query.delete()

        # Faz o commit da remoção antes da inserção
        db.session.commit()

        # Insere os novos dados em massa
        db.session.bulk_insert_mappings(model, data)

        # Faz o commit da inserção
        db.session.commit()

        # Log de status
        _log_status(model.query.count(), label)
        # except Exception as e:
        #     # Em caso de erro, faz rollback
        #     db.session.rollback()
        #     print(f"Erro ao realizar a inserção em massa: {e}")
        # finally:
        #     db.session.close()


    return None


@click.group()
def cli():
    """ Add items to the database. """
    pass


@click.command()
def users():
    """
    Generate fake users.
    """
    random_emails = []
    data = []

    click.echo('Working...')

    # Ensure we get about 100 unique random emails.
    for i in range(0, 99):
        random_emails.append(fake.email())

    random_emails.append(app.config['SEED_ADMIN_EMAIL'])
    random_emails = list(set(random_emails))

    while True:
        if len(random_emails) == 0:
            break

        fake_datetime = fake.date_time_between(
            start_date='-1y', end_date='now').strftime('%s')

        created_on = datetime.utcfromtimestamp(
            float(fake_datetime)).strftime('%Y-%m-%dT%H:%M:%S Z')

        random_percent = random.random()

        if random_percent >= 0.05:
            role = 'member'
        else:
            role = 'admin'

        email = random_emails.pop()

        random_percent = random.random()

        if random_percent >= 0.5:
            random_trail = str(int(round((random.random() * 1000))))
            username = fake.first_name() + random_trail
        else:
            username = None

        fake_datetime = fake.date_time_between(
            start_date='-1y', end_date='now').strftime('%s')

        current_sign_in_on = datetime.utcfromtimestamp(
            float(fake_datetime)).strftime('%Y-%m-%dT%H:%M:%S Z')

        params = {
            'created_on': created_on,
            'updated_on': created_on,
            'role': role,
            'email': email,
            'username': username,
            'password': User.encrypt_password('password'),
            'sign_in_count': random.random() * 100,
            'current_sign_in_on': current_sign_in_on,
            'current_sign_in_ip': fake.ipv4(),
            'last_sign_in_on': current_sign_in_on,
            'last_sign_in_ip': fake.ipv4()
        }

        # Ensure the seeded admin is always an admin with the seeded password.
        if email == app.config['SEED_ADMIN_EMAIL']:
            password = User.encrypt_password(app.config['SEED_ADMIN_PASSWORD'])

            params['role'] = 'admin'
            params['password'] = password

        data.append(params)

    return _bulk_insert(User, data, 'users')

@click.command()
def invoices():
    """
    Generate random invoices.
    """
    data = []

    # Garante que o comando rode dentro do contexto de aplicação do Flask
    # app = create_app()  # Crie sua app Flask, se ainda não tiver feito isso
    with app.app_context():
        users = db.session.query(User).all()

        for user in users:
            for i in range(0, random.randint(1, 12)):
                # Create a fake unix timestamp in the future.
                # created_on = fake.date_time_between(start_date='-1y', end_date='now').strftime('%s')
                # period_start_on = fake.date_time_between(start_date='now', end_date='+1y').strftime('%s')
                # period_end_on = fake.date_time_between(start_date=period_start_on, end_date='+14d').strftime('%s')
                # exp_date = fake.date_time_between(start_date='now', end_date='+2y').strftime('%s')

                # created_on = datetime.utcfromtimestamp(float(created_on)).strftime('%Y-%m-%dT%H:%M:%S Z')
                # period_start_on = datetime.utcfromtimestamp(float(period_start_on)).strftime('%Y-%m-%d')
                # period_end_on = datetime.utcfromtimestamp(float(period_end_on)).strftime('%Y-%m-%d')
                # exp_date = datetime.utcfromtimestamp(float(exp_date)).strftime('%Y-%m-%d')

                created_on = fake.date_time_between(start_date='-1y', end_date='now').strftime('%s')
                period_start_on = fake.date_time_between(start_date='now', end_date='+1y').strftime('%s')
                exp_date = fake.date_time_between(start_date='now', end_date='+2y').strftime('%s')

                created_on = datetime.utcfromtimestamp(float(created_on)).strftime('%Y-%m-%dT%H:%M:%S Z')
                period_start_on_date = datetime.utcfromtimestamp(float(period_start_on))  # Convert to datetime object
                period_start_on = period_start_on_date.strftime('%Y-%m-%d')
                
                # Now use the converted datetime object for `start_date`
                period_end_on = fake.date_time_between(start_date=period_start_on_date, end_date='+14d').strftime('%s')
                period_end_on = datetime.utcfromtimestamp(float(period_end_on)).strftime('%Y-%m-%d')

                exp_date = datetime.utcfromtimestamp(float(exp_date)).strftime('%Y-%m-%d')

                plans = ['BRONZE', 'GOLD', 'PLATINUM']
                cards = ['Visa', 'Mastercard', 'AMEX',
                        'J.C.B', "Diner's Club"]

                params = {
                    'created_on': created_on,
                    'updated_on': created_on,
                    'user_id': user.id,
                    'receipt_number': fake.md5(),
                    'description': '{0} MONTHLY'.format(random.choice(plans)),
                    'period_start_on': period_start_on,
                    'period_end_on': period_end_on,
                    'currency': 'usd',
                    'tax': random.random() * 100,
                    'tax_percent': random.random() * 10,
                    'total': random.random() * 1000,
                    'brand': random.choice(cards),
                    'last4': random.randint(1000, 9000),
                    'exp_date': exp_date
                }

                data.append(params)

    return _bulk_insert(Invoice, data, 'invoices')

@click.command()
@click.pass_context
def all(ctx):
    """
    Generate all data.

    :param ctx:
    :return: None
    """
    ctx.invoke(users)
    ctx.invoke(invoices)

    return None


cli.add_command(users)
cli.add_command(invoices)
cli.add_command(all)
