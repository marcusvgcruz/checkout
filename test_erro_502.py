"""Teste de regressão: erro do MercadoPago deve virar 502 com mensagem.

Bug (achado da Afrodite no QA): o handler faz HTTPException(502, detail=(err)),
passando o OBJETO RuntimeError. A serialização JSON falha e o cliente recebe
500 genérico em vez de 502 com a mensagem.
"""
import os

os.environ.setdefault('MP_BASE_API_URL', 'https://api.mercadopago.com/')
os.environ.setdefault('MP_ACCESS_TOKEN', 'TEST-0000000000000000')
os.environ.setdefault('MP_PUBLIC_KEY', 'TEST-0000000000000000')

from unittest.mock import patch

from fastapi.testclient import TestClient

import app as app_module
from app import app


client = TestClient(app, raise_server_exceptions=False)

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


@patch.object(app_module.mp, '_MercadoPago__get_card_token',
              side_effect=RuntimeError('Erro MP 400: cartão recusado'))
def test_erro_mp_vira_502_com_mensagem(mock_token):
    """RuntimeError do MP deve virar 502 com a mensagem no detail, não 500."""
    response = client.post('/create_payment', json=CARD_PAYLOAD)

    body = response.json()
    assert response.status_code == 502, (
        f'esperado 502, veio {response.status_code}: {body}'
    )
    detail = body.get('detail')
    assert isinstance(detail, str), f'detail deve ser string, veio {type(detail)}: {detail!r}'
    assert 'cartão recusado' in detail, f'mensagem do erro perdida: {detail!r}'
