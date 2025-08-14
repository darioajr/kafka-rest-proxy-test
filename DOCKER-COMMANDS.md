# 🐳 Comandos Docker para POC Kafka

## 🚀 INÍCIO RÁPIDO

### 1. **Iniciar Ambiente Kafka**
```bash
docker-compose up -d
```

### 2. **Verificar Status**
```bash
docker-compose ps
```

### 3. **Aguardar Inicialização (2-3 minutos)**
```bash
# Aguardar todos os serviços ficarem healthy
docker-compose ps | grep healthy
```

---

## 🧪 EXECUTAR TESTES

### 🔥 **Teste Básico (1K mensagens)**
```bash
docker-compose --profile testing run --rm test-basic
```

### 🏎️ **Teste Otimizado (50K mensagens)**
```bash
docker-compose --profile testing run --rm test-optimized
```

### ⚡ **Teste Extremo (100K mensagens)**
```bash
docker-compose --profile testing run --rm test-extreme
```

### 📦 **Teste Mensagens 64KB**
```bash
docker-compose --profile testing run --rm test-64kb
```

---

## 🎛️ TESTES CUSTOMIZADOS

### **Teste Básico Personalizado**
```bash
docker run --rm --network kafka-teste_kafka-network \
  $(docker build -q -f Dockerfile.tests .) \
  scripts/load-test.py \
  --messages 5000 \
  --concurrency 20 \
  --topic meu-topico \
  --url http://kafka-rest-proxy:8082
```

### **Teste Performance Personalizado**
```bash
docker run --rm --network kafka-teste_kafka-network \
  $(docker build -q -f Dockerfile.tests .) \
  scripts/optimized-load-test.py \
  --messages 200000 \
  --concurrency 300 \
  --batch-size 800 \
  --topic performance-test \
  --url http://kafka-rest-proxy:8082
```

---

## 📊 COMANDOS DE MONITORAMENTO

### **Logs em Tempo Real**
```bash
# Logs do Kafka
docker-compose logs -f kafka

# Logs do REST Proxy
docker-compose logs -f kafka-rest-proxy

# Logs de todos os serviços
docker-compose logs -f
```

### **Verificar Tópicos**
```bash
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092
```

### **Criar Tópico Personalizado**
```bash
docker-compose exec kafka kafka-topics \
  --create \
  --bootstrap-server localhost:9092 \
  --topic meu-topico \
  --partitions 24 \
  --replication-factor 1 \
  --config compression.type=lz4
```

---

## 🛑 PARAR E LIMPAR

### **Parar Ambiente**
```bash
docker-compose down
```

### **Parar e Limpar Dados**
```bash
docker-compose down -v
```

### **Limpar Imagens de Teste**
```bash
docker rmi $(docker images -q -f "dangling=true")
```

---

## 🔧 TROUBLESHOOTING DOCKER

### **Rebuildar Imagens**
```bash
docker-compose build --no-cache
```

### **Forçar Recriação**
```bash
docker-compose up -d --force-recreate
```

### **Verificar Redes**
```bash
docker network ls | grep kafka
```

### **Verificar Volumes**
```bash
docker volume ls | grep kafka
```

---

## 📈 TESTES DE PERFORMANCE PROGRAMADOS

### **Sequência Completa de Testes**
```bash
#!/bin/bash
echo "🚀 Iniciando sequência completa de testes..."

# 1. Iniciar ambiente
docker-compose up -d
sleep 120  # Aguardar inicialização

# 2. Teste básico
echo "🧪 Executando teste básico..."
docker-compose --profile testing run --rm test-basic

# 3. Teste otimizado
echo "🏎️ Executando teste otimizado..."
docker-compose --profile testing run --rm test-optimized

# 4. Teste extremo
echo "⚡ Executando teste extremo..."
docker-compose --profile testing run --rm test-extreme

# 5. Teste 64KB
echo "📦 Executando teste 64KB..."
docker-compose --profile testing run --rm test-64kb

echo "✅ Sequência de testes concluída!"
```

---

## 🎯 COMANDOS ÚNICOS (ONE-LINERS)

### **Setup + Teste Rápido**
```bash
docker-compose up -d && sleep 120 && docker-compose --profile testing run --rm test-basic
```

### **Teste Performance Completo**
```bash
docker-compose up -d && sleep 120 && docker-compose --profile testing run --rm test-optimized && docker-compose --profile testing run --rm test-extreme
```

### **Reset Completo**
```bash
docker-compose down -v && docker-compose up -d
```

---

## 💡 DICAS DOCKER

- Use `--profile testing` para ativar os serviços de teste
- Use `--rm` para remover containers após execução
- Use `-d` para executar em background
- Use `-f` para seguir logs em tempo real
- Use `--no-cache` para rebuilds limpos
