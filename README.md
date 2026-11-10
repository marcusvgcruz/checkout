# Checkout — Mercado Pago

API em FastAPI com uma página de checkout que aceita pagamento por cartão de
crédito, PIX e boleto, usando a API de pagamentos do Mercado Pago. A página é
servida pelo próprio backend, e a resposta da API volta inteira em JSON, com os
dados de cada forma de pagamento.

## Fluxo do checkout

1. `GET /` entrega o formulário (`templates/checkout.html`) com as três formas de
   pagamento. Os campos de cartão, PIX e boleto aparecem conforme a escolha.
2. O navegador envia o formulário para `POST /create_payment` em JSON.
3. O backend chama o Mercado Pago:
   - **Cartão**: cria primeiro o token do cartão (`POST /v1/card_tokens`) e
     depois o pagamento (`POST /v1/payments`) com o token e o número de parcelas;
   - **PIX**: cria o pagamento com `payment_method_id: pix` e devolve o link do
     QR Code;
   - **Boleto**: cria o pagamento com `payment_method_id: bolbradesco` e devolve
     a URL do boleto.
4. Cada chamada leva um header `X-Idempotency-Key` com UUID novo.
5. Se o Mercado Pago recusar a chamada, o backend devolve `502` com o código e o
   corpo do erro.
6. No navegador: cartão mostra aprovado ou recusado conforme o `status`; PIX e
   boleto redirecionam para a página de pagamento do Mercado Pago.

## Stack

- FastAPI 0.162 com Uvicorn
- Jinja2 para o template do checkout
- Requests para falar com a API do Mercado Pago
- python-decouple para ler as variáveis do `.env`
- Tailwind via CDN no template

## Como rodar

```bash
git clone https://github.com/marcusvgcruz/checkout.git
cd checkout

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env     # preencha o MP_ACCESS_TOKEN

uvicorn app:app --reload
```

Abra `http://127.0.0.1:8000/`.

## Variáveis de ambiente

| Variável | Para que serve |
| :--- | :--- |
| `MP_BASE_API_URL` | base da API do Mercado Pago: `https://api.mercadopago.com/` |
| `MP_ACCESS_TOKEN` | access token da conta que recebe o pagamento |
| `MP_PUBLIC_KEY` | aparece no `.env.example`; o backend atual não lê essa variável |

O número do cartão é enviado ao backend, que cria o token no servidor. A chave
pública não é usada porque a tokenização acontece do lado do servidor.

## Endpoints

### `GET /`

Página do checkout.

### `POST /create_payment`

Corpo em JSON. Os campos mudam conforme `payment_method`.

Cartão:

```json
{
  "payment_method": "card",
  "transaction_amount": 100,
  "description": "Pedido 123",
  "card_number": "5031 4332 1540 6351",
  "expiration_mounth": "11",
  "expiration_year": "2030",
  "security_code": "123",
  "cardholder_name": "NOME NO CARTAO",
  "identification_number": "12345678900",
  "installments": 1,
  "email": "cliente@exemplo.com"
}
```

PIX:

```json
{
  "payment_method": "pix",
  "transaction_amount": 100,
  "description": "Pedido 123",
  "email": "cliente@exemplo.com",
  "identification_number": "12345678900"
}
```

Boleto:

```json
{
  "payment_method": "boleto",
  "transaction_amount": 100,
  "description": "Pedido 123",
  "email": "cliente@exemplo.com",
  "identification_number": "12345678900",
  "first_name": "Joao",
  "last_name": "Silva",
  "zip_code": "01001000",
  "street_name": "Praca da Se",
  "street_number": "100",
  "neighborhood": "Se",
  "city": "Sao Paulo",
  "federal_unit": "SP"
}
```

A resposta é o JSON do Mercado Pago: o `status` do pagamento para cartão,
`point_of_interaction.transaction_data.ticket_url` para PIX e
`transaction_details.external_resource_url` para boleto.

## Observações de sandbox

- Use as credenciais de teste do Mercado Pago (chaves que começam com `TEST-`)
  para rodar sem movimentar dinheiro. Quem define o modo é o access token.
- O formulário vem com valor `100` e descrição "Teste de Pagamento" como padrão,
  o que ajuda nos testes de sandbox.
- Não coloque token real no repositório: o `.env` não é versionado.
- O Mercado Pago exige número de cartão e CPF válidos no ambiente de teste; use
  os cartões de teste da documentação deles.
- Para produção, vale tokenizar o cartão no navegador (MercadoPago.js) em vez de
  enviar o número para o backend como o template faz hoje.

## Estrutura

```
app.py                   rotas da API e da página
services/mercadopago.py  client da API do Mercado Pago
templates/checkout.html  formulário e script do checkout
```

## Licença

Repositório pessoal de Marcus Cruz, sem licença declarada.
