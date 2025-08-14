#!/usr/bin/env python3
"""
Script de teste de carga otimizado baseado na análise de performance
Inclui retry automático, timeouts otimizados e melhor tratamento de erros
"""

import asyncio
import aiohttp
import time
import json
import argparse
import statistics
from datetime import datetime

class OptimizedKafkaLoadTester:
    def __init__(self, rest_proxy_url="http://localhost:8082"):
        self.rest_proxy_url = rest_proxy_url
        self.results = {
            "success_count": 0,
            "error_count": 0,
            "response_times": [],
            "errors_by_type": {},
            "retries_performed": 0
        }
    
    def generate_batch_message(self, batch_size, start_id, thread_id):
        """Gera um batch de mensagens otimizado"""
        records = []
        for i in range(batch_size):
            msg_id = start_id + i
            records.append({
                "key": f"optimized-key-{msg_id}",
                "value": {
                    "id": msg_id,
                    "thread": thread_id,
                    "message": f"Mensagem otimizada {msg_id}",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "batch_id": start_id // batch_size,
                    "test_type": "optimized_load_test"
                }
            })
        
        return {"records": records}
    
    async def send_batch_with_retry(self, session, topic, batch_data, retry_count=3):
        """Envia batch com retry automático e backoff exponencial"""
        headers = {
            'Content-Type': 'application/vnd.kafka.json.v2+json',
            'Accept': 'application/vnd.kafka.v2+json'
        }
        
        batch_size = len(batch_data["records"])
        
        for attempt in range(retry_count):
            start_time = time.time()
            try:
                # Timeout progressivo baseado na tentativa
                timeout_seconds = 5 + (attempt * 2)
                
                async with session.post(
                    f"{self.rest_proxy_url}/topics/{topic}",
                    json=batch_data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=timeout_seconds)
                ) as response:
                    response_time = (time.time() - start_time) * 1000
                    self.results["response_times"].append(response_time)
                    
                    if response.status == 200:
                        self.results["success_count"] += batch_size
                        if attempt > 0:
                            self.results["retries_performed"] += 1
                        return True, response_time
                    else:
                        error_text = await response.text()
                        if attempt == retry_count - 1:  # Último retry
                            self.results["error_count"] += batch_size
                            error_key = f"HTTP_{response.status}"
                            self.results["errors_by_type"][error_key] = self.results["errors_by_type"].get(error_key, 0) + 1
                            print(f"X Erro final {response.status} após {retry_count} tentativas")
                        else:
                            print(f"! Tentativa {attempt + 1} falhou (HTTP {response.status}), tentando novamente...")
                            await asyncio.sleep(0.1 * (2 ** attempt))  # Backoff exponencial
                            
            except asyncio.TimeoutError:
                response_time = (time.time() - start_time) * 1000
                self.results["response_times"].append(response_time)
                if attempt == retry_count - 1:
                    self.results["error_count"] += batch_size
                    self.results["errors_by_type"]["Timeout"] = self.results["errors_by_type"].get("Timeout", 0) + 1
                    print(f"X Timeout final após {retry_count} tentativas")
                else:
                    print(f"! Timeout na tentativa {attempt + 1}, tentando novamente...")
                    await asyncio.sleep(0.2 * (2 ** attempt))
                    
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                self.results["response_times"].append(response_time)
                if attempt == retry_count - 1:
                    self.results["error_count"] += batch_size
                    error_key = f"Exception_{type(e).__name__}"
                    self.results["errors_by_type"][error_key] = self.results["errors_by_type"].get(error_key, 0) + 1
                    print(f"X Exceção final: {str(e)[:50]}...")
                else:
                    print(f"! Exceção na tentativa {attempt + 1}: {type(e).__name__}")
                    await asyncio.sleep(0.1 * (2 ** attempt))
        
        return False, 0
    
    async def run_optimized_test(self, topic, total_messages, concurrency, batch_size):
        """Executa teste de carga otimizado"""
        print("=== TESTE DE CARGA OTIMIZADO ===")
        print(f"Tópico: {topic}")
        print(f"Total de mensagens: {total_messages}")
        print(f"Concorrência: {concurrency}")
        print(f"Tamanho do batch: {batch_size}")
        print(f"REST Proxy: {self.rest_proxy_url}")
        print("=" * 40)
        
        start_time = time.time()
        
        # Configurar conector com pool de conexões otimizado
        connector = aiohttp.TCPConnector(
            limit=concurrency * 2,  # Pool de conexões
            limit_per_host=concurrency * 2,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        async with aiohttp.ClientSession(connector=connector) as session:
            # Verificar conectividade
            try:
                async with session.get(f"{self.rest_proxy_url}/topics", timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status != 200:
                        print(f"ERRO: REST Proxy retornou status {response.status}")
                        return
                print("✓ Conectividade verificada")
            except Exception as e:
                print(f"ERRO: Não foi possível conectar ao REST Proxy: {e}")
                return
            
            # Criar tasks de envio
            tasks = []
            message_id = 1
            
            # Distribuir mensagens em batches
            for thread_id in range(concurrency):
                messages_per_thread = total_messages // concurrency
                if thread_id < total_messages % concurrency:
                    messages_per_thread += 1
                
                # Criar batches para esta thread
                thread_batches = messages_per_thread // batch_size
                remaining = messages_per_thread % batch_size
                
                for batch_num in range(thread_batches):
                    batch_data = self.generate_batch_message(batch_size, message_id, thread_id)
                    task = self.send_batch_with_retry(session, topic, batch_data)
                    tasks.append(task)
                    message_id += batch_size
                
                # Batch final com mensagens restantes
                if remaining > 0:
                    batch_data = self.generate_batch_message(remaining, message_id, thread_id)
                    task = self.send_batch_with_retry(session, topic, batch_data)
                    tasks.append(task)
                    message_id += remaining
            
            print(f"Executando {len(tasks)} batches com retry automático...")
            
            # Executar com progresso
            completed = 0
            for task in asyncio.as_completed(tasks):
                await task
                completed += 1
                if completed % 10 == 0:
                    progress = (completed / len(tasks)) * 100
                    print(f"Progresso: {progress:.1f}% ({completed}/{len(tasks)} batches)")
        
        end_time = time.time()
        duration = end_time - start_time
        
        self.print_optimized_results(duration, total_messages)
    
    def print_optimized_results(self, duration, total_messages):
        """Imprime resultados otimizados com análise detalhada"""
        throughput = self.results["success_count"] / duration if duration > 0 else 0
        
        print("\n" + "=" * 60)
        print("RESULTADOS DO TESTE OTIMIZADO")
        print("=" * 60)
        print(f"Tempo total: {duration:.2f}s")
        print(f"Mensagens processadas: {total_messages}")
        print(f"Sucessos: {self.results['success_count']}")
        print(f"Erros: {self.results['error_count']}")
        print(f"Retries realizados: {self.results['retries_performed']}")
        
        if total_messages > 0:
            success_rate = (self.results['success_count'] / total_messages) * 100
            print(f"Taxa de sucesso: {success_rate:.2f}%")
        
        print(f"Throughput: {throughput:.2f} msg/s")
        
        # Análise de erros
        if self.results["errors_by_type"]:
            print(f"\nERROS POR TIPO:")
            for error_type, count in self.results["errors_by_type"].items():
                print(f"  {error_type}: {count}")
        
        # Estatísticas de tempo de resposta
        if self.results["response_times"]:
            print(f"\nTEMPOS DE RESPOSTA (ms):")
            times = self.results["response_times"]
            print(f"Mínimo: {min(times):.2f}")
            print(f"Máximo: {max(times):.2f}")
            print(f"Média: {statistics.mean(times):.2f}")
            print(f"Mediana: {statistics.median(times):.2f}")
            
            if len(times) > 1:
                print(f"Desvio padrão: {statistics.stdev(times):.2f}")
            
            # Percentis
            sorted_times = sorted(times)
            if len(sorted_times) >= 10:
                p95_index = int(0.95 * len(sorted_times))
                p99_index = int(0.99 * len(sorted_times))
                print(f"P95: {sorted_times[p95_index]:.2f}")
                print(f"P99: {sorted_times[p99_index]:.2f}")
        
        # Recomendações baseadas nos resultados
        print(f"\nRECOMENDAÇÕES:")
        if success_rate < 95:
            print("- Taxa de sucesso baixa: considere reduzir concorrência ou aumentar timeouts")
        if throughput < 100:
            print("- Throughput baixo: considere aumentar batch size ou verificar recursos")
        if self.results["retries_performed"] > 0:
            print(f"- {self.results['retries_performed']} retries foram necessários: considere otimizar configurações")
        
        print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description='Teste de carga otimizado para Kafka REST Proxy')
    parser.add_argument('--messages', type=int, default=1000, help='Número total de mensagens')
    parser.add_argument('--concurrency', type=int, default=10, help='Número de threads concorrentes')
    parser.add_argument('--topic', type=str, default='test', help='Nome do tópico')
    parser.add_argument('--batch-size', type=int, default=10, help='Tamanho do batch')
    parser.add_argument('--url', type=str, default='http://localhost:8082', help='URL do REST Proxy')
    
    args = parser.parse_args()
    
    tester = OptimizedKafkaLoadTester(args.url)
    
    try:
        asyncio.run(tester.run_optimized_test(
            args.topic,
            args.messages,
            args.concurrency,
            args.batch_size
        ))
    except KeyboardInterrupt:
        print("\n\nTeste interrompido pelo usuário")

if __name__ == "__main__":
    main()
