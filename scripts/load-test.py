#!/usr/bin/env python3
"""
Script de teste de carga para Kafka REST Proxy
Uso: python load-test.py [--messages 1000] [--concurrency 10] [--topic test] [--batch-size 10]
"""

import argparse
import asyncio
import aiohttp
import json
import time
import random
import string
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import statistics

class KafkaLoadTester:
    def __init__(self, rest_proxy_url="http://localhost:8082"):
        self.rest_proxy_url = rest_proxy_url
        self.success_count = 0
        self.error_count = 0
        self.response_times = []
        
    def generate_message(self, msg_id, thread_id):
        """Gera uma mensagem de teste"""
        return {
            "records": [
                {
                    "key": f"key-{msg_id}",
                    "value": {
                        "id": msg_id,
                        "thread": thread_id,
                        "message": f"Mensagem de teste {msg_id} do thread {thread_id}",
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "random_data": ''.join(random.choices(string.ascii_letters + string.digits, k=100)),
                        "payload_size": "medium",
                        "test_run": int(time.time())
                    }
                }
            ]
        }
    
    async def send_message_async(self, session, topic, msg_id, thread_id):
        """Envia uma mensagem de forma assíncrona"""
        message = self.generate_message(msg_id, thread_id)
        headers = {
            'Content-Type': 'application/vnd.kafka.json.v2+json',
            'Accept': 'application/vnd.kafka.v2+json'
        }
        
        start_time = time.time()
        try:
            async with session.post(
                f"{self.rest_proxy_url}/topics/{topic}",
                json=message,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                response_time = (time.time() - start_time) * 1000  # em ms
                self.response_times.append(response_time)
                
                if response.status == 200:
                    self.success_count += 1
                    return True, response_time
                else:
                    self.error_count += 1
                    error_text = await response.text()
                    print(f"✗ Erro {response.status} na mensagem {msg_id}: {error_text}")
                    return False, response_time
                    
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.response_times.append(response_time)
            self.error_count += 1
            print(f"✗ Exceção na mensagem {msg_id}: {str(e)}")
            return False, response_time
    
    async def run_batch(self, session, topic, batch_messages, thread_id):
        """Executa um lote de mensagens"""
        tasks = []
        for msg_id in batch_messages:
            task = self.send_message_async(session, topic, msg_id, thread_id)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    
    async def run_load_test(self, topic, total_messages, concurrency, batch_size):
        """Executa o teste de carga principal"""
        print(f"=== Iniciando Teste de Carga ===")
        print(f"Tópico: {topic}")
        print(f"Total de mensagens: {total_messages}")
        print(f"Concorrência: {concurrency}")
        print(f"Tamanho do batch: {batch_size}")
        print(f"REST Proxy: {self.rest_proxy_url}")
        print("=" * 40)
        
        start_time = time.time()
        
        # Criar batches de mensagens
        message_batches = []
        for i in range(0, total_messages, batch_size):
            batch = list(range(i + 1, min(i + batch_size + 1, total_messages + 1)))
            message_batches.append(batch)
        
        # Distribuir batches entre threads
        batches_per_thread = len(message_batches) // concurrency
        remaining_batches = len(message_batches) % concurrency
        
        async with aiohttp.ClientSession() as session:
            # Verificar conectividade
            try:
                async with session.get(f"{self.rest_proxy_url}/topics") as response:
                    if response.status != 200:
                        print(f"ERRO: REST Proxy retornou status {response.status}")
                        return
                print("✓ Conectividade com REST Proxy verificada")
            except Exception as e:
                print(f"ERRO: Não foi possível conectar ao REST Proxy: {e}")
                return
            
            # Executar batches em paralelo
            tasks = []
            batch_index = 0
            
            for thread_id in range(concurrency):
                thread_batches = batches_per_thread
                if thread_id < remaining_batches:
                    thread_batches += 1
                
                for _ in range(thread_batches):
                    if batch_index < len(message_batches):
                        batch = message_batches[batch_index]
                        task = self.run_batch(session, topic, batch, thread_id + 1)
                        tasks.append(task)
                        batch_index += 1
            
            print(f"Executando {len(tasks)} batches...")
            
            # Executar todas as tasks
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
        end_time = time.time()
        duration = end_time - start_time
        
        # Calcular estatísticas
        self.print_results(duration, total_messages)
    
    def print_results(self, duration, total_messages):
        """Imprime os resultados do teste"""
        throughput = total_messages / duration if duration > 0 else 0
        
        print("\n" + "=" * 50)
        print("RESULTADOS DO TESTE DE CARGA")
        print("=" * 50)
        print(f"Tempo total: {duration:.2f}s")
        print(f"Mensagens enviadas: {total_messages}")
        print(f"Sucessos: {self.success_count}")
        print(f"Erros: {self.error_count}")
        print(f"Taxa de sucesso: {(self.success_count/total_messages)*100:.2f}%")
        print(f"Throughput: {throughput:.2f} msg/s")
        
        if self.response_times:
            print(f"\nTEMPOS DE RESPOSTA (ms):")
            print(f"Mínimo: {min(self.response_times):.2f}")
            print(f"Máximo: {max(self.response_times):.2f}")
            print(f"Média: {statistics.mean(self.response_times):.2f}")
            print(f"Mediana: {statistics.median(self.response_times):.2f}")
            
            if len(self.response_times) > 1:
                print(f"Desvio padrão: {statistics.stdev(self.response_times):.2f}")
            
            # Percentis
            sorted_times = sorted(self.response_times)
            p95_index = int(0.95 * len(sorted_times))
            p99_index = int(0.99 * len(sorted_times))
            
            print(f"P95: {sorted_times[p95_index]:.2f}")
            print(f"P99: {sorted_times[p99_index]:.2f}")
        
        print("=" * 50)

def main():
    parser = argparse.ArgumentParser(description='Teste de carga para Kafka REST Proxy')
    parser.add_argument('--messages', type=int, default=1000, help='Número total de mensagens (padrão: 1000)')
    parser.add_argument('--concurrency', type=int, default=10, help='Número de threads concorrentes (padrão: 10)')
    parser.add_argument('--topic', type=str, default='test', help='Nome do tópico (padrão: test)')
    parser.add_argument('--batch-size', type=int, default=10, help='Tamanho do batch (padrão: 10)')
    parser.add_argument('--url', type=str, default='http://localhost:8082', help='URL do REST Proxy')
    
    args = parser.parse_args()
    
    tester = KafkaLoadTester(args.url)
    
    try:
        asyncio.run(tester.run_load_test(
            args.topic,
            args.messages,
            args.concurrency,
            args.batch_size
        ))
    except KeyboardInterrupt:
        print("\n\nTeste interrompido pelo usuário")
        tester.print_results(0, args.messages)

if __name__ == "__main__":
    main()
