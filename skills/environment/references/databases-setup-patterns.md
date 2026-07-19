# Padrões de Configuração de Banco de Dados

## PostgreSQL 18.4

### Serviço no Compose

```yaml
postgres:
  image: postgres:18
  environment:
    POSTGRES_DB: ${DB_NAME}
    POSTGRES_USER: ${DB_USER}
    POSTGRES_PASSWORD: ${DB_PASSWORD}
  volumes:
    - postgres_data:/var/lib/postgresql/data
    - ./init-scripts/postgres:/docker-entrypoint-initdb.d
  ports:
    - "${DB_PORT:-5432}:5432"
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
    interval: 5s
    timeout: 3s
    retries: 5
    start_period: 10s
```

### Scripts de inicialização

Os arquivos em `/docker-entrypoint-initdb.d/` são executados apenas na primeira execução (em ordem alfabética).
Formatos suportados: `.sql`, `.sql.gz`, `.sh`

```sql
-- 01-extensions.sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "hstore";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
```

```sql
-- 02-schema.sql
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_users_email ON users USING btree(email);
CREATE INDEX idx_users_name_trgm ON users USING gin(name gin_trgm_ops);
```

### Migrações (Alembic)

```bash
# Setup
pip install alembic==1.15.2
alembic init alembic

# Generate from model changes
alembic revision --autogenerate -m "description"

# Apply
alembic upgrade head

# Rollback one step
alembic downgrade -1

# View current state
alembic current
alembic history
```

### String de conexão

```
postgresql://user:password@host:5432/dbname
```

### Comandos úteis do psql

```bash
docker compose exec postgres psql -U ${DB_USER} -d ${DB_NAME}

\dt           # list tables
\d+ tablename # describe table with details
\di           # list indexes
\l            # list databases
\conninfo     # connection info
```

---

## MongoDB 8.2.3

### Serviço no Compose

```yaml
mongo:
  image: mongo:8.2.3
  environment:
    MONGO_INITDB_ROOT_USERNAME: ${MONGO_USER}
    MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD}
    MONGO_INITDB_DATABASE: ${MONGO_DB}
  volumes:
    - mongo_data:/data/db
    - ./init-scripts/mongo:/docker-entrypoint-initdb.d
  ports:
    - "${MONGO_PORT:-27017}:27017"
  healthcheck:
    test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
    interval: 5s
    timeout: 3s
    retries: 5
```

### Scripts de inicialização

```javascript
// 01-init.js
db = db.getSiblingDB(process.env.MONGO_INITDB_DATABASE || 'app');

// Create collections with validation
db.createCollection('users', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['email', 'name'],
      properties: {
        email: { bsonType: 'string' },
        name: { bsonType: 'string' },
        role: { enum: ['admin', 'user'] }
      }
    }
  }
});

// Create indexes
db.users.createIndex({ email: 1 }, { unique: true });
db.users.createIndex({ created_at: -1 });
db.users.createIndex({ name: 'text' });

// Seed data
db.users.insertMany([
  { email: 'admin@example.com', name: 'Admin', role: 'admin', created_at: new Date() },
  { email: 'test@example.com', name: 'Test User', role: 'user', created_at: new Date() }
]);
```

### String de conexão

```
mongodb://user:password@host:27017/dbname?authSource=admin
```

### Comandos úteis do mongosh

```bash
docker compose exec mongo mongosh -u ${MONGO_USER} -p ${MONGO_PASSWORD}

show dbs
use mydb
show collections
db.users.find().pretty()
db.users.countDocuments()
db.users.getIndexes()
```

---

## Redis 8.4.2

### Serviço no Compose

```yaml
redis:
  image: redis:8.4.2-alpine
  command: >
    redis-server
    --requirepass ${REDIS_PASSWORD}
    --appendonly yes
    --maxmemory 256mb
    --maxmemory-policy allkeys-lru
  volumes:
    - redis_data:/data
  ports:
    - "${REDIS_PORT:-6379}:6379"
  healthcheck:
    test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
    interval: 5s
    timeout: 3s
    retries: 5
```

### Opções de configuração

| Opção | Valor | Propósito |
|--------|-------|---------|
| `--appendonly yes` | Persistência AOF | Durabilidade (log de escrita) |
| `--maxmemory 256mb` | Limite de memória | Evita OOM |
| `--maxmemory-policy allkeys-lru` | Política de despejo | Remove os itens menos usados recentemente |
| `--requirepass` | Senha | Autenticação básica |
| `--save 60 1000` | Snapshots RDB | Snapshot a cada 60s se houver 1000+ escritas |

### String de conexão

```
redis://:password@host:6379/0
```

### Comandos úteis do redis-cli

```bash
docker compose exec redis redis-cli -a ${REDIS_PASSWORD}

PING                    # test connection
INFO server             # server info
INFO memory             # memory usage
DBSIZE                  # number of keys
KEYS *                  # list all keys (dev only!)
FLUSHDB                 # clear current database
MONITOR                 # real-time command stream
```

---

## Resetar os Dados do Banco

```bash
# Stop services
docker compose down

# Remove specific volume
docker volume rm myproject_postgres_data

# Or remove all project volumes
docker compose down -v

# Recreate (init scripts run again)
docker compose up -d
```
