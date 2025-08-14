@echo off
REM 🚀 Script de Automação - POC Kafka Alta Performance (Windows)
REM Uso: kafka-test.bat [comando] [opções]

setlocal enabledelayedexpansion

if "%1"=="" goto :help
if "%1"=="help" goto :help
if "%1"=="-h" goto :help
if "%1"=="--help" goto :help

REM Verificar se Docker está rodando
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker não está rodando. Inicie o Docker primeiro.
    exit /b 1
)

if "%1"=="start" goto :start
if "%1"=="stop" goto :stop
if "%1"=="restart" goto :restart
if "%1"=="status" goto :status
if "%1"=="logs" goto :logs
if "%1"=="clean" goto :clean
if "%1"=="test-basic" goto :test-basic
if "%1"=="test-optimized" goto :test-optimized
if "%1"=="test-extreme" goto :test-extreme
if "%1"=="test-64kb" goto :test-64kb
if "%1"=="test-all" goto :test-all
if "%1"=="topics" goto :topics
if "%1"=="create-topic" goto :create-topic
if "%1"=="monitor" goto :monitor
if "%1"=="quick-start" goto :quick-start
if "%1"=="performance-test" goto :performance-test

echo ❌ Comando desconhecido: %1
goto :help

:start
echo ℹ️  Iniciando ambiente Kafka...
docker-compose up -d
echo ✅ Ambiente Kafka iniciado!
echo ℹ️  Acesse Kafka UI: http://localhost:8080
goto :eof

:stop
echo ℹ️  Parando ambiente Kafka...
docker-compose down
echo ✅ Ambiente parado!
goto :eof

:restart
echo ℹ️  Reiniciando ambiente Kafka...
docker-compose down
docker-compose up -d
echo ✅ Ambiente reiniciado!
goto :eof

:status
echo ℹ️  Status dos serviços:
docker-compose ps
goto :eof

:logs
echo ℹ️  Mostrando logs (Ctrl+C para sair):
docker-compose logs -f
goto :eof

:clean
echo ⚠️  Limpando dados do Kafka...
docker-compose down -v
echo ✅ Dados limpos!
goto :eof

:test-basic
echo ℹ️  Executando teste básico...
docker-compose --profile testing run --rm test-basic
echo ✅ Teste básico concluído!
goto :eof

:test-optimized
echo ℹ️  Executando teste otimizado...
docker-compose --profile testing run --rm test-optimized
echo ✅ Teste otimizado concluído!
goto :eof

:test-extreme
echo ℹ️  Executando teste extremo...
docker-compose --profile testing run --rm test-extreme
echo ✅ Teste extremo concluído!
goto :eof

:test-64kb
echo ℹ️  Executando teste 64KB...
docker-compose --profile testing run --rm test-64kb
echo ✅ Teste 64KB concluído!
goto :eof

:test-all
echo ℹ️  Executando sequência completa de testes...
echo ℹ️  1/4 - Teste básico...
docker-compose --profile testing run --rm test-basic
echo ℹ️  2/4 - Teste otimizado...
docker-compose --profile testing run --rm test-optimized
echo ℹ️  3/4 - Teste extremo...
docker-compose --profile testing run --rm test-extreme
echo ℹ️  4/4 - Teste 64KB...
docker-compose --profile testing run --rm test-64kb
echo ✅ Todos os testes concluídos!
goto :eof

:topics
echo ℹ️  Listando tópicos:
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092
goto :eof

:create-topic
if "%2"=="" (
    echo ❌ Uso: kafka-test.bat create-topic NOME_DO_TOPICO [PARTICOES]
    exit /b 1
)
set TOPIC_NAME=%2
if "%3"=="" (
    set PARTITIONS=24
) else (
    set PARTITIONS=%3
)
echo ℹ️  Criando tópico '%TOPIC_NAME%' com %PARTITIONS% partições...
docker-compose exec kafka kafka-topics --create --bootstrap-server localhost:9092 --topic %TOPIC_NAME% --partitions %PARTITIONS% --replication-factor 1 --config compression.type=lz4
echo ✅ Tópico '%TOPIC_NAME%' criado!
goto :eof

:monitor
echo ℹ️  Monitorando performance...
echo ℹ️  Kafka UI: http://localhost:8080
echo ℹ️  REST Proxy: http://localhost:8082
echo ℹ️  Schema Registry: http://localhost:8081
echo ℹ️  Pressione Ctrl+C para sair do monitoramento
docker-compose logs -f kafka kafka-rest-proxy
goto :eof

:quick-start
echo 🚀 QUICK START - Iniciando ambiente e teste básico...
docker-compose up -d
timeout /t 120 /nobreak >nul
echo ✅ Ambiente iniciado!
echo ℹ️  Executando teste básico...
docker-compose --profile testing run --rm test-basic
echo ✅ Quick start concluído!
goto :eof

:performance-test
echo 🏎️ TESTE DE PERFORMANCE COMPLETO...
echo ℹ️  Executando teste otimizado...
docker-compose --profile testing run --rm test-optimized
echo ℹ️  Executando teste extremo...
docker-compose --profile testing run --rm test-extreme
echo ✅ Teste de performance concluído!
goto :eof

:help
echo 🚀 POC Kafka - Comandos Disponíveis
echo.
echo AMBIENTE:
echo   start          Iniciar ambiente Kafka
echo   stop           Parar ambiente
echo   restart        Reiniciar ambiente
echo   status         Verificar status dos serviços
echo   logs           Mostrar logs dos serviços
echo   clean          Parar e limpar dados
echo.
echo TESTES:
echo   test-basic     Teste básico (1K msgs)
echo   test-optimized Teste otimizado (50K msgs)
echo   test-extreme   Teste extremo (100K msgs)
echo   test-64kb      Teste mensagens 64KB
echo   test-all       Executar todos os testes
echo.
echo UTILITÁRIOS:
echo   topics         Listar tópicos
echo   create-topic   Criar tópico personalizado
echo   monitor        Monitorar performance
echo   quick-start    Início rápido (start + teste básico)
echo   performance-test  Teste de performance completo
echo.
echo Exemplos:
echo   kafka-test.bat start
echo   kafka-test.bat test-optimized
echo   kafka-test.bat test-all
goto :eof
