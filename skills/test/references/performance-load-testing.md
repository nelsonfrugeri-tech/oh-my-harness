# Teste de Carga

## Perfis de Carga
| Perfil | Padrão | Objetivo |
|---------|---------|---------|
| Ramp-up | Aumento gradual de 0→N usuários | Encontrar o ponto de ruptura |
| Spike | Rajada repentina | Testar auto-scaling e tratamento de erros |
| Soak | Carga constante por horas | Encontrar vazamentos de memória e esgotamento de conexões |
| Stress | Além da capacidade esperada | Encontrar os modos de falha |

## Exemplo com k6
```javascript
// load-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 100 },   // ramp up
    { duration: '5m', target: 100 },   // steady
    { duration: '2m', target: 200 },   // spike
    { duration: '5m', target: 0 },     // ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<200', 'p(99)<500'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const res = http.get('http://localhost:3000/api/users');
  check(res, { 'status 200': (r) => r.status === 200 });
  sleep(1);
}
```

## Exemplo com Locust (Python)
```python
from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def list_users(self):
        self.client.get("/api/users")
    
    @task(1)
    def create_user(self):
        self.client.post("/api/users", json={"name": "test"})
```

## Métricas a Observar
- Tempo de resposta (p50, p95, p99)
- Taxa de erros
- Throughput (req/s)
- Utilização de recursos (CPU, memória, conexões)

## Ferramentas: k6 0.54+ (2026), Locust 2.32+ (2026)
