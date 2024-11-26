from flask import Blueprint, render_template

from api.painel.blueprints.wallet.models.wallet import Wallet

wallet_bp = Blueprint('wallet', __name__, url_prefix='/wallet')

@wallet_bp.route('/wallet/<int:user_id>', methods=['GET'])
def wallet_history(user_id):
    """
    Exibe o histórico de transações da carteira de um usuário.
    """
    transactions = Wallet.transaction_history(user_id)
    return render_template('wallet/list.html', transactions=transactions)
