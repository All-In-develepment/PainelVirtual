import datetime

import stripe

from lib.util_datetime import timedelta_months
from lib.util_sqlalchemy import ResourceMixin
from painel.extensions import db


class CreditCard(ResourceMixin, db.Model):
    IS_EXPIRING_THRESHOLD_MONTHS = 2

    __tablename__ = 'credit_cards'
    id = db.Column(db.Integer, primary_key=True)

    # Relationships.
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', onupdate='CASCADE', ondelete='CASCADE'), index=True, nullable=False)

    # Card details.
    brand = db.Column(db.String(32))
    last4 = db.Column(db.Integer)
    exp_date = db.Column(db.Date, index=True)
    is_expiring = db.Column(db.Boolean(), nullable=False, server_default='0')

    def __init__(self, **kwargs):
        # Call Flask-SQLAlchemy's constructor.
        super(CreditCard, self).__init__(**kwargs)

    @classmethod
    def is_expiring_soon(cls, compare_date=None, exp_date=None):
        """
        Determine whether or not this credit card is expiring soon.

        :param compare_date: Date to compare at
        :type compare_date: date
        :param exp_date: Expiration date
        :type exp_date: date
        :return: bool
        """
        return exp_date <= timedelta_months(
            CreditCard.IS_EXPIRING_THRESHOLD_MONTHS, compare_date=compare_date)

    @classmethod
    def mark_old_credit_cards(cls, compare_date=None):
        """
        Mark credit cards that are going to expire soon or have expired.

        :param compare_date: Date to compare at
        :type compare_date: date
        :return: Result of updating the records
        """
        today_with_delta = timedelta_months(
            CreditCard.IS_EXPIRING_THRESHOLD_MONTHS, compare_date)

        CreditCard.query.filter(CreditCard.exp_date <= today_with_delta).update({CreditCard.is_expiring: True})

        return db.session.commit()

    @classmethod
    def extract_card_params(cls, customer):
        print(customer)
        """
        Extract the credit card info from a payment customer object.

        :param customer: Payment customer
        :type customer: Payment customer
        :return: dict or None
        """

        # card_data = customer.sources.data[0]
        customer_id = customer.id
        # Lista todos os métodos de pagamento do tipo "card" associados ao cliente
        payment_methods = stripe.PaymentMethod.list(
            customer=customer_id,
            type="card"
        )
        # Verifica se há métodos de pagamento associados
        if len(payment_methods.data) == 0:
            print("Nenhum método de pagamento associado ao cliente.")
        else:
            # Exibe os métodos de pagamento encontrados
            card_data = payment_methods.data[0].card
            exp_date = datetime.date(card_data.exp_year, card_data.exp_month, 1)

        card = {
            'brand': card_data.brand,
            'last4': card_data.last4,
            'exp_date': exp_date,
            'is_expiring': CreditCard.is_expiring_soon(exp_date=exp_date)
        }

        return card
