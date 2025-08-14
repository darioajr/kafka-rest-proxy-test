#!/bin/bash

# 🚀 Script de Automação - POC Kafka Alta Performance
# Uso: ./kafka-test.sh [comando] [opções]

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para logs coloridos
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Função para verificar se Docker está rodando
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker não está rodando. Inicie o Docker primeiro."
        exit 1
    fi
}

# Função para aguardar serviços ficarem healthy
wait_for_healthy() {
    log_info "Aguardando serviços ficarem healthy..."
    local max_attempts=60
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        local healthy_count=$(docker-compose ps --filter "health=healthy" --quiet | wc -l)
        if [ "$healthy_count" -ge 3 ]; then
            log_success "Todos os serviços estão healthy!"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    log_error "Timeout aguardando serviços ficarem healthy"
    return 1
}

# Função para mostrar ajuda
show_help() {
    echo "🚀 POC Kafka - Comandos Disponíveis"
    echo ""
    echo "AMBIENTE:"
    echo "  start          Iniciar ambiente Kafka"
    echo "  stop           Parar ambiente"
    echo "  restart        Reiniciar ambiente"
    echo "  status         Verificar status dos serviços"
    echo "  logs           Mostrar logs dos serviços"
    echo "  clean          Parar e limpar dados"
    echo ""
    echo "TESTES:"
    echo "  test-basic     Teste básico (1K msgs)"
    echo "  test-optimized Teste otimizado (50K msgs)"
    echo "  test-extreme   Teste extremo (100K msgs)"
    echo "  test-64kb      Teste mensagens 64KB"
    echo "  test-all       Executar todos os testes"
    echo ""
    echo "UTILITÁRIOS:"
    echo "  topics         Listar tópicos"
    echo "  create-topic   Criar tópico personalizado"
    echo "  monitor        Monitorar performance"
    echo ""
    echo "Exemplos:"
    echo "  ./kafka-test.sh start"
    echo "  ./kafka-test.sh test-optimized"
    echo "  ./kafka-test.sh test-all"
}

# Comandos principais
case "$1" in
    "start")
        log_info "Iniciando ambiente Kafka..."
        check_docker
        docker-compose up -d
        wait_for_healthy
        log_success "Ambiente Kafka iniciado!"
        log_info "Acesse Kafka UI: http://localhost:8080"
        ;;
        
    "stop")
        log_info "Parando ambiente Kafka..."
        docker-compose down
        log_success "Ambiente parado!"
        ;;
        
    "restart")
        log_info "Reiniciando ambiente Kafka..."
        docker-compose down
        docker-compose up -d
        wait_for_healthy
        log_success "Ambiente reiniciado!"
        ;;
        
    "status")
        log_info "Status dos serviços:"
        docker-compose ps
        ;;
        
    "logs")
        log_info "Mostrando logs (Ctrl+C para sair):"
        docker-compose logs -f
        ;;
        
    "clean")
        log_warning "Limpando dados do Kafka..."
        docker-compose down -v
        log_success "Dados limpos!"
        ;;
        
    "test-basic")
        log_info "Executando teste básico..."
        docker-compose --profile testing run --rm test-basic
        log_success "Teste básico concluído!"
        ;;
        
    "test-optimized")
        log_info "Executando teste otimizado..."
        docker-compose --profile testing run --rm test-optimized
        log_success "Teste otimizado concluído!"
        ;;
        
    "test-extreme")
        log_info "Executando teste extremo..."
        docker-compose --profile testing run --rm test-extreme
        log_success "Teste extremo concluído!"
        ;;
        
    "test-64kb")
        log_info "Executando teste 64KB..."
        docker-compose --profile testing run --rm test-64kb
        log_success "Teste 64KB concluído!"
        ;;
        
    "test-all")
        log_info "Executando sequência completa de testes..."
        
        log_info "1/4 - Teste básico..."
        docker-compose --profile testing run --rm test-basic
        
        log_info "2/4 - Teste otimizado..."
        docker-compose --profile testing run --rm test-optimized
        
        log_info "3/4 - Teste extremo..."
        docker-compose --profile testing run --rm test-extreme
        
        log_info "4/4 - Teste 64KB..."
        docker-compose --profile testing run --rm test-64kb
        
        log_success "Todos os testes concluídos!"
        ;;
        
    "topics")
        log_info "Listando tópicos:"
        docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092
        ;;
        
    "create-topic")
        if [ -z "$2" ]; then
            log_error "Uso: ./kafka-test.sh create-topic NOME_DO_TOPICO [PARTICOES]"
            exit 1
        fi
        
        TOPIC_NAME="$2"
        PARTITIONS="${3:-24}"
        
        log_info "Criando tópico '$TOPIC_NAME' com $PARTITIONS partições..."
        docker-compose exec kafka kafka-topics \
            --create \
            --bootstrap-server localhost:9092 \
            --topic "$TOPIC_NAME" \
            --partitions "$PARTITIONS" \
            --replication-factor 1 \
            --config compression.type=lz4
        log_success "Tópico '$TOPIC_NAME' criado!"
        ;;
        
    "monitor")
        log_info "Monitorando performance..."
        log_info "Kafka UI: http://localhost:8080"
        log_info "REST Proxy: http://localhost:8082"
        log_info "Schema Registry: http://localhost:8081"
        log_info ""
        log_info "Pressione Ctrl+C para sair do monitoramento"
        docker-compose logs -f kafka kafka-rest-proxy
        ;;
        
    "quick-start")
        log_info "🚀 QUICK START - Iniciando ambiente e teste básico..."
        check_docker
        docker-compose up -d
        wait_for_healthy
        log_success "Ambiente iniciado!"
        
        log_info "Executando teste básico..."
        docker-compose --profile testing run --rm test-basic
        log_success "✅ Quick start concluído!"
        ;;
        
    "performance-test")
        log_info "🏎️ TESTE DE PERFORMANCE COMPLETO..."
        check_docker
        
        # Verificar se ambiente está rodando
        if ! docker-compose ps | grep -q "Up.*healthy"; then
            log_info "Iniciando ambiente..."
            docker-compose up -d
            wait_for_healthy
        fi
        
        log_info "Executando teste otimizado..."
        docker-compose --profile testing run --rm test-optimized
        
        log_info "Executando teste extremo..."
        docker-compose --profile testing run --rm test-extreme
        
        log_success "✅ Teste de performance concluído!"
        ;;
        
    "" | "help" | "--help" | "-h")
        show_help
        ;;
        
    *)
        log_error "Comando desconhecido: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
