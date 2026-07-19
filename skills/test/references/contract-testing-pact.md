# Testes de Contrato Orientados ao Consumidor com Pact

## Conceito
O consumer define as interações esperadas → gera o contrato (arquivo pact) → o provider verifica em relação a ele.

## Fluxo
```
1. Consumer writes test defining expected request/response
2. Pact generates contract file (JSON)
3. Contract published to Pact Broker
4. Provider runs verification against contract
5. Can-I-Deploy check before releasing
```

## Exemplo de Consumer em Python
```python
# consumer_test.py
from pact import Consumer, Provider

pact = Consumer("OrderService").has_pact_with(Provider("PaymentService"))

def test_get_payment():
    expected = {"id": "pay-123", "status": "completed", "amount": 99.99}
    
    pact.given("payment exists")
    pact.upon_receiving("a request for payment")
    pact.with_request("GET", "/payments/pay-123")
    pact.will_respond_with(200, body=expected)
    
    with pact:
        result = payment_client.get_payment("pay-123")
        assert result["status"] == "completed"
```

## Quando Usar
- Microsserviços com APIs REST/GraphQL
- Múltiplos times são donos de serviços diferentes
- Necessidade de confiança de que mudanças na API não quebram os consumers

## Quando NÃO Usar
- Monólito (use testes de integração)
- Um único time é dono de todos os serviços
- Assíncrono/orientado a eventos (use um schema registry em vez disso)

## Ferramentas: Pact 5.x (2026), Pact Broker, can-i-deploy CLI
