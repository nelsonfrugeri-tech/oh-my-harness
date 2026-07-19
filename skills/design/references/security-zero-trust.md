# Arquitetura de Segurança

## Princípios de Zero Trust
1. **Nunca confie, sempre verifique** — toda requisição é autenticada e autorizada
2. **Menor privilégio** — o acesso mínimo necessário para a tarefa
3. **Assuma o comprometimento** — projete para contenção, não apenas prevenção
4. **Verifique explicitamente** — identidade, dispositivo, localização, classificação dos dados

## Defesa em Profundidade
```
Layer 1: Network (firewalls, segmentation, mTLS)
Layer 2: Identity (authn, authz, MFA, JWT validation)
Layer 3: Application (input validation, CSRF, CORS, rate limiting)
Layer 4: Data (encryption at rest, encryption in transit, masking)
Layer 5: Monitoring (audit logs, anomaly detection, SIEM)
```

## Threat Modeling com STRIDE
| Ameaça | Propriedade violada | Mitigação |
|--------|------------------|------------|
| Spoofing | Autenticação | MFA, autenticação forte |
| Tampering | Integridade | Validação de entrada, assinatura |
| Repudiation | Não-repúdio | Audit logging |
| Information disclosure | Confidencialidade | Criptografia, controle de acesso |
| Denial of service | Disponibilidade | Rate limiting, CDN |
| Elevation of privilege | Autorização | RBAC, menor privilégio |

## Checklist de Implementação
- [ ] TLS em todo lugar (sem HTTP)
- [ ] Validação de JWT em toda requisição
- [ ] RBAC/ABAC para autorização
- [ ] Sanitização de entrada nas fronteiras
- [ ] Secrets em vault, nunca em código/config
- [ ] Scanning de dependências (Snyk, Dependabot)
- [ ] Audit logging para operações sensíveis
