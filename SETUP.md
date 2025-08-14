# 🛠️ Setup da POC Kafka

## 📋 Pré-requisitos

### 🐳 Docker
- Docker Desktop ou Docker Engine
- Docker Compose v2+
- Mínimo 8GB RAM disponível
- Mínimo 4 CPU cores

### 🐍 Python
- Python 3.8+
- pip para instalação de dependências

## 🚀 Instalação

### 1. **Dependências Python**
```bash
pip install aiohttp asyncio argparse statistics
```

### 2. **Verificar Docker**
```bash
docker --version
docker-compose --version
```

### 3. **Clonar/Baixar Projeto**
Certifique-se de ter todos os arquivos da POC:
- `docker-compose.yml`
- `scripts/*.py`
- `README.md`

## ⚡ Execução Rápida

### 🚀 **Start Completo**
```bash
# 1. Iniciar ambiente
docker-compose up -d

# 2. Aguardar inicialização (2-3 minutos)
docker-compose ps

# 3. Teste básico
python scripts/load-test.py --messages 1000 --concurrency 10

# 4. Teste de performance
python scripts/optimized-load-test.py --messages 50000 --concurrency 200
```

### 🛑 **Stop Completo**
```bash
# Parar ambiente
docker-compose down

# Limpar dados (opcional)
docker-compose down -v
```

## 🔧 Troubleshooting

### ❌ **Problemas Comuns**

#### 1. **OutOfMemoryError**
```bash
# Reduzir concorrência
python scripts/optimized-load-test.py --concurrency 100

# Ou reduzir batch size
python scripts/optimized-load-test.py --batch-size 500
```

#### 2. **Connection Timeout**
```bash
# Aguardar mais tempo para inicialização
sleep 60

# Verificar se todos os containers estão healthy
docker-compose ps
```

#### 3. **Port Already in Use**
```bash
# Verificar processos usando as portas
netstat -an | grep :8082
netstat -an | grep :9092

# Matar processos se necessário
docker-compose down
```

### ✅ **Verificações de Saúde**

#### **Verificar Kafka**
```bash
curl -s http://localhost:8082/topics
```

#### **Verificar Schema Registry**
```bash
curl -s http://localhost:8081/subjects
```

#### **Verificar Kafka UI**
Acessar: http://localhost:8080

## 📊 Parâmetros de Teste

### 🎛️ **Configurações Recomendadas**

#### **Teste de Desenvolvimento**
```bash
python scripts/load-test.py --messages 1000 --concurrency 10
```

#### **Teste de Performance**
```bash
python scripts/optimized-load-test.py --messages 50000 --concurrency 200 --batch-size 500
```

#### **Teste de Limite**
```bash
python scripts/extreme-50k-test.py --messages 100000 --concurrency 500 --batch-size 1000
```

#### **Teste de Mensagens Grandes**
```bash
python scripts/working-64kb-test.py --messages 500 --concurrency 20 --batch-size 5
```

### ⚙️ **Ajuste de Parâmetros**

- **--messages**: Total de mensagens (1K - 1M)
- **--concurrency**: Conexões simultâneas (10 - 500)
- **--batch-size**: Mensagens por batch (10 - 1000)
- **--topic**: Nome do tópico (padrão: test)

## 🎯 Resultados Esperados

### ✅ **Performance Targets**

| Teste | Target | Hardware |
|-------|--------|----------|
| Básico | 3K+ msg/s | 4 cores, 8GB |
| Otimizado | 20K+ msg/s | 8 cores, 16GB |
| Extremo | 40K+ msg/s | 16 cores, 32GB |

### 📈 **Métricas de Sucesso**
- Taxa de sucesso: 100%
- Latência P95: < 3 segundos
- Sem OutOfMemoryError
- Throughput sustentado

## 🆘 Suporte

### 🔍 **Logs de Debug**
```bash
# Logs do Kafka
docker logs kafka

# Logs do REST Proxy
docker logs kafka-rest-proxy

# Logs do Schema Registry
docker logs schema-registry
```

### 📞 **Contato**
- Verificar logs de erro nos containers
- Validar recursos de sistema (CPU, RAM)
- Confirmar versões do Docker e Python
