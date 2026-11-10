"""Testes do endpoint de pagamento do checkout.

Cobrem o bug de typo: o template envia `expiration_month` mas o app lia
`expiration_mounth`, mandando None para o MercadoPago.
"""
import os

# MercadoPago lê as variáveis na importação (decouple), então precisam existir
# antes de importar o app.
os.environ.setdefault('MP_BASE_API_URL', 'https://api.mercadopago.com/')
os.environ.setdefault('MP_ACCESS_TOKEN', 'TEST-0000000000000000')
os.environ.setdefault('MP_PUBLIC_KEY', 'TEST-0000000000000000')

from unittest.mock import patch

from fastapi.testclient import TestClient

import app as app_module
from app import app


client = TestClient(app)

CARD_PAYLOAD = {
    'payment_method': 'card',
    'transaction_amount': 100,
    'description': 'Pedido 123',
    'card_number': '5031 4332 1540 6351',
    'expiration_month': '11',
    'expiration_year': '2030',
    'security_code': '123',
    'cardholder_name': 'NOME NO CARTAO',
    'identification_number': '12345678900',
    'installments': 1,
    'email': 'cliente@exemplo.com',
}


@patch.object(app_module.mp, '_MercadoPago__create_payment', return_value={'status': 'approved'})
@patch.object(app_module.mp, '_MercadoPago__get_card_token', return_value='tok_test')
def test_card_envia_expiration_month_correto(mock_token, mock_payment):
    """O card_data enviado ao MercadoPago deve ter expiration_month com o valor do form."""
    response = client.post('/create_payment', json=CARD_PAYLOAD)

    assert response.status_code == 200
    assert response.json()['status'] == 'approved'

    # __get_card_token recebe o card_data montado pelo endpoint
    card_data = mock_token.call_args.args[0] if mock_token.call_args.args else mock_token.call_args.kwargs['card_data']
    assert 'expiration_month' in card_data, 'card_data deve usar expiration_month (sem typo)'
    assert 'expiration_mounth' not in card_data, 'não deve restar o typo expiration_mounth'
    assert card_data['expiration_month'] == '11'
    assert card_data['expiration_year'] == '2030'


@patch.object(app_module.mp, '_MercadoPago__create_payment', return_value={'status': 'approved'})
@patch.object(app_module.mp, '_MercadoPago__get_card_token', return_value='tok_test')
def test_payload_do_template_é_consumido(mock_token, mock_payment):
    """O JSON que o template monta (FormData -> payload) é lido integralmente."""
    response = client.post('/create_payment', json=CARD_PAYLOAD)

    assert response.status_code == 200
    card_data = mock_token.call_args.args[0]
    assert card_data['card_number'] == CARD_PAYLOAD['card_number']
    assert card_data['security_code'] == '123'
    assert card_data['cardholder']['name'] == 'NOME NO CARTAO'
    assert card_data['cardholder']['identification']['number'] == '12345678900'


def test_metodo_invalido_retorna_400():
    response = client.post('/create_payment', json={'payment_method': 'dinheiro'})
    assert response.status_code == 400
    assert 'inválido' in response.json()['detail']
