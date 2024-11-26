

from collections import OrderedDict
from painel.extensions import db
from api.lib.util_sqlalchemy import ResourceMixin


class Wallet(ResourceMixin, db.Model):
  KIND = OrderedDict([
    ('deposito', 'Deposito'),
    ('aposta', 'Aposta'),
    ('saque', 'Saque')
  ])
  
  RESULT = OrderedDict([
    ('red', 'Red'),
    ('green', 'Green')
  ])
  
  __tablename__ = 'wallets'

  id = db.Column(db.Integer, primary_key=True)

  kind = db.Column(db.Enum(*KIND, name='kinds_type', native_enum=False), index=True, nullable=False)

  value = db.Column(db.Float())
  
  result = db.Column(db.Enum(*RESULT, name='results_type', native_enum=False), index=True, nullable=False)
  
  odd = db.Column(db.Float())
  
  betting_return = db.Column(db.Float())
  
  balance  = db.Column(db.Float())
  
  data = db.Column(db.String(255))
  
  user_id = db.Column(db.Integer, db.ForeignKey('users.id', onupdate='CASCADE', ondelete='CASCADE'), index=True, nullable=False)
  
  def __init__(self, **kwargs):
    # Call Flask-SQLAlchemy's constructor.
    super(Wallet, self).__init__(**kwargs)
    
  @classmethod
  def transaction_history(cls, user=None):
      """
      Return the transaction history for a specific user.

      :param user: User whose transaction history will be retrieved
      :type user: User instance

      :return: Wallet transactions
      """
      transactions = Wallet.query.filter(Wallet.user_id == user.id) \
          .order_by(Wallet.created_on.desc()).all()

      return transactions


  @classmethod
  def parse_from_event(cls, payload):
      """
      Parse and return the transaction information that will get saved locally.

      :return: dict
      """
      transaction = {
          'kind': payload.get('kind'),  # Tipo da transação (ex.: deposito, saque)
          'value': payload.get('value'),  # Valor da transação
          'result': payload.get('result'),  # Resultado (ex.: green ou red)
          'odd': payload.get('odd'),  # Odds da aposta
          'betting_return': payload.get('betting_return'),  # Retorno da aposta
          'balance': payload.get('balance'),  # Saldo atual
          'data': payload.get('data'),  # Dados adicionais
          'user_id': payload.get('user_id')  # Usuário associado
      }

      return transaction
    
  @classmethod
  def prepare_and_save(cls, parsed_event):
      """
      Potentially save the transaction after augmenting the event fields.

      :param parsed_event: Event params to be saved
      :type parsed_event: dict
      :return: Wallet instance
      """
      wallet_transaction = Wallet(**parsed_event)
      wallet_transaction.save()
      return wallet_transaction
    
  @classmethod
  def calculate_balance(cls, user=None):
      """
      Calculate the current balance for a specific user.

      :param user: User whose balance will be calculated
      :type user: User instance

      :return: float
      """
      transactions = Wallet.query.filter(Wallet.user_id == user.id).all()
      balance = sum([t.value if t.kind == 'deposito' else -t.value for t in transactions])
      return balance