# Procedimentos de Recuperação de Erros

## Problemas com Docker
| Erro | Correção |
|-------|-----|
| Porta já em uso | `lsof -i :PORT` e depois `kill <PID>`, ou troque a porta |
| Sem espaço em disco | `docker system prune -a --volumes` (ATENÇÃO: remove tudo) |
| Container não inicia | Verifique os logs: `docker logs <id>`, corrija a config, refaça o build |
| Cache de build desatualizado | `docker compose build --no-cache service` |
| Conflito de rede | `docker network prune` e depois recrie |

## Problemas com Banco de Dados
| Erro | Correção |
|-------|-----|
| PostgreSQL "role does not exist" | Verifique POSTGRES_USER no env, recrie o volume |
| Falha de autenticação no MongoDB | Garanta que MONGO_INITDB_ROOT_USERNAME corresponda à connection string |
| Redis maxmemory | Defina `maxmemory-policy allkeys-lru` no redis.conf |
| Migração falhou | Verifique o estado da migração, `migrate down` e depois reaplique |
| Volume corrompido | `docker volume rm <vol>` e refaça o seed |

## Reset Total
```bash
# Stop everything, remove volumes, rebuild
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

## Prevenção
- Sempre use volumes nomeados (não anônimos)
- Health checks em todos os serviços
- Scripts de seed idempotentes (seguros para reexecutar)
- Fixe as versões das imagens (nunca use :latest em dev)
