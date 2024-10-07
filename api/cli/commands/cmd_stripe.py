import click

from painel.app import create_app
from painel.extensions import db
from painel.blueprints.billing.gateways.stripecom import Plan as PaymentPlan, Product

# Create an app context for the database connection.
app = create_app()
db.app = app


@click.group()
def cli():
    """ Perform various tasks with Stripe's API. """
    pass

# Criação de produtos na stripe
@click.command()
def creat_products():
    """
    Create STRIPE_PRODUCTS on Stripe.

    :return: None
    """
    if app.config['STRIPE_PRODUCTS'] is None:
        return None

    for _, value in app.config['STRIPE_PRODUCTS'].items():
        product = Product.retrieve(value.get('id'))

        if product:
            Product.update(id=value.get('id'),
                                name=value.get('name'),
                                metadata=value.get('metadata'),
                                )
        else:
            Product.create(**value)

    return None

# Listagem de produtos na stripe
@click.command()
def list_products():
    """
    List all existing products on Stripe.

    :return: Stripe products
    """
    click.echo(Product.list())

@click.command()
def sync_plans():
    """
    Sync (upsert) STRIPE_PLANS to Stripe.

    :return: None
    """
    if app.config['STRIPE_PLANS'] is None:
        return None

    for _, value in app.config['STRIPE_PLANS'].items():
        plan = PaymentPlan.retrieve(value.get('id'))

        if plan:
            PaymentPlan.update(id=value.get('id'),
                                name=value.get('name'),
                                metadata=value.get('metadata'),
                                )
        else:
            PaymentPlan.create(**value)

    return None


@click.command()
@click.argument('plan_ids', nargs=-1)
def delete_plans(plan_ids):
    """
    Delete 1 or more plans from Stripe.

    :return: None
    """
    for plan_id in plan_ids:
        PaymentPlan.delete(plan_id)

    return None


@click.command()
def list_plans():
    """
    List all existing plans on Stripe.

    :return: Stripe plans
    """
    click.echo(PaymentPlan.list())


cli.add_command(sync_plans)
cli.add_command(delete_plans)
cli.add_command(list_plans)
cli.add_command(creat_products)
cli.add_command(list_products)
