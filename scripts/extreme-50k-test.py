#!/usr/bin/env python3
"""
TESTE EXTREMO para 50K+ msg/s - Configurações no limite máximo
Ultra-otimizado para throughput máximo
"""

import asyncio
import aiohttp
import time
import json
import argparse
import statistics
import random
import string
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import threading

class ExtremePerformanceKafkaLoadTester:
    def __init__(self, rest_proxy_url="http://localhost:8082"):
        self.rest_proxy_url = rest_proxy_url
        self.results = {
            "success_count": 0,
            "error_count": 0,
            "response_times": [],
            "errors_by_type": {},
            "bytes_sent": 0,
            "requests_sent": 0
        }
        self.lock = threading.Lock()
        
        # Cache de mensagens pré-geradas para máxima performance
        self.message_cache = {}
        
    def pre_generate_messages(self, cache_size=1000):
        """Pré-gera mensagens para cache e máxima performance"""
        print(f"🔥 Pré-gerando {cache_size} mensagens para cache...")
        
        base_data = ''.join(random.choices(string.ascii_letters + string.digits, k=100))
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        for i in range(cache_size):
            self.message_cache[i] = {
                "id": i,
                "message": f"Extreme performance test message {i}",
                "timestamp": timestamp,
                "data": base_data,
                "sequence": i,
                "thread_marker": "extreme-test"
            }
        
        print(f"✅ Cache de {cache_size} mensagens criado")
    
    def generate_extreme_batch(self, batch_size, start_id, thread_id):
        """Gera batch usando cache para máxima velocidade"""
        records = []
        
        for i in range(batch_size):
            msg_id = start_id + i
            cache_key = msg_id % len(self.message_cache)
            
            # Usar mensagem do cache com ID atualizado
            cached_msg = self.message_cache[cache_key].copy()
            cached_msg["id"] = msg_id
            cached_msg["thread"] = thread_id
            
            records.append({
                "key": f"extreme-{msg_id}",
                "value": cached_msg
            })
        
        return {"records": records}
    
    async def send_extreme_batch(self, session, topic, batch_data, semaphore):
        """Envio ultra-otimizado sem retry para máxima velocidade"""
        async with semaphore:
            batch_size = len(batch_data["records"])
            
            # Pré-serializar JSON para economia de CPU
            payload = json.dumps(batch_data)
            payload_size = len(payload.encode('utf-8'))
            
            with self.lock:
                self.results["bytes_sent"] += payload_size
                self.results["requests_sent"] += 1
            
            start_time = time.time()
            
            try:
                async with session.post(
                    f"{self.rest_proxy_url}/topics/{topic}",
                    data=payload,
                    headers={
                        'Content-Type': 'application/vnd.kafka.json.v2+json',
                        'Accept': 'application/vnd.kafka.v2+json'
                    },
                    timeout=aiohttp.ClientTimeout(total=5),  # Timeout agressivo
                    compress=False  # Desabilitar compressão HTTP para velocidade
                ) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    with self.lock:
                        self.results["response_times"].append(response_time)
                    
                    if response.status == 200:
                        with self.lock:
                            self.results["success_count"] += batch_size
                        return True
                    else:
                        with self.lock:
                            self.results["error_count"] += batch_size
                            error_key = f"HTTP_{response.status}"
                            self.results["errors_by_type"][error_key] = self.results["errors_by_type"].get(error_key, 0) + 1
                        return False
                        
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                with self.lock:
                    self.results["response_times"].append(response_time)
                    self.results["error_count"] += batch_size
                    error_key = f"Exception_{type(e).__name__}"
                    self.results["errors_by_type"][error_key] = self.results["errors_by_type"].get(error_key, 0) + 1
                return False
    
    async def run_extreme_test(self, topic, total_messages, concurrency, batch_size):
        """Teste extremo para 50K+ msg/s"""
        print("🔥 === TESTE EXTREMO PARA 50K+ MSG/S ===")
        print(f"Tópico: {topic}")
        print(f"Total de mensagens: {total_messages:,}")
        print(f"Concorrência: {concurrency}")
        print(f"Tamanho do batch: {batch_size}")
        print(f"REST Proxy: {self.rest_proxy_url}")
        print("=" * 50)
        
        # Pré-gerar cache de mensagens
        self.pre_generate_messages(1000)
        
        # Semáforo ultra-agressivo
        semaphore = asyncio.Semaphore(concurrency)
        
        start_time = time.time()
        
        # Configurar conector para máxima performance
        connector = aiohttp.TCPConnector(
            limit=concurrency * 4,
            limit_per_host=concurrency * 4,
            keepalive_timeout=300,
            enable_cleanup_closed=True,
            use_dns_cache=True,
            ttl_dns_cache=600,
            family=0,
            ssl=False,
            force_close=False
        )
        
        timeout = aiohttp.ClientTimeout(total=10, connect=1)
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'Connection': 'keep-alive',
                'Keep-Alive': 'timeout=300, max=1000'
            }
        ) as session:
            
            # Verificação de conectividade mínima
            try:
                async with session.get(f"{self.rest_proxy_url}/topics", timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status != 200:
                        print(f"❌ ERRO: REST Proxy status {response.status}")
                        return
                print("✅ Conectividade extrema verificada")
            except Exception as e:
                print(f"❌ ERRO: {e}")
                return
            
            # Gerar todas as tasks de uma vez (modo extremo)
            total_batches = total_messages // batch_size
            if total_messages % batch_size > 0:
                total_batches += 1
            
            print(f"🚀 Gerando {total_batches:,} batches para modo EXTREMO...")
            
            # Processar em chunks grandes para máxima velocidade
            chunk_size = min(500, total_batches)
            processed_batches = 0
            
            for chunk_start in range(0, total_batches, chunk_size):
                chunk_end = min(chunk_start + chunk_size, total_batches)
                chunk_tasks = []
                
                # Gerar tasks do chunk
                for batch_num in range(chunk_start, chunk_end):
                    start_id = batch_num * batch_size + 1
                    current_batch_size = min(batch_size, total_messages - (batch_num * batch_size))
                    
                    if current_batch_size <= 0:
                        break
                    
                    thread_id = batch_num % concurrency
                    batch_data = self.generate_extreme_batch(current_batch_size, start_id, thread_id)
                    
                    task = self.send_extreme_batch(session, topic, batch_data, semaphore)
                    chunk_tasks.append(task)
                
                # Executar chunk em modo extremo
                if chunk_tasks:
                    chunk_start_time = time.time()
                    await asyncio.gather(*chunk_tasks, return_exceptions=True)
                    chunk_duration = time.time() - chunk_start_time
                    
                    processed_batches += len(chunk_tasks)
                    
                    # Estatísticas em tempo real
                    progress = (processed_batches / total_batches) * 100
                    elapsed = time.time() - start_time
                    
                    if elapsed > 0:
                        current_throughput = self.results["success_count"] / elapsed
                        current_rps = self.results["requests_sent"] / elapsed
                        
                        print(f"⚡ Progresso: {progress:.1f}% | "
                              f"Throughput: {current_throughput:,.0f} msg/s | "
                              f"RPS: {current_rps:,.0f} | "
                              f"Batches: {processed_batches:,}/{total_batches:,} | "
                              f"Chunk: {chunk_duration:.2f}s")
        
        end_time = time.time()
        duration = end_time - start_time
        
        self.print_extreme_results(duration, total_messages)
    
    def print_extreme_results(self, duration, total_messages):
        """Relatório de resultados extremos"""
        throughput = self.results["success_count"] / duration if duration > 0 else 0
        
        print("\n" + "🔥" + "=" * 70)
        print("RESULTADOS EXTREMOS - TESTE DE LIMITE MÁXIMO")
        print("=" * 72)
        print(f"⏱️  Tempo total: {duration:.3f}s")
        print(f"📤 Mensagens enviadas: {total_messages:,}")
        print(f"✅ Sucessos: {self.results['success_count']:,}")
        print(f"❌ Erros: {self.results['error_count']:,}")
        print(f"📊 Taxa de sucesso: {(self.results['success_count']/total_messages)*100:.3f}%")
        print(f"🚀 THROUGHPUT: {throughput:,.2f} msg/s")
        
        # Análise de dados
        total_mb = self.results['bytes_sent'] / 1024 / 1024
        print(f"💾 Dados enviados: {total_mb:.2f} MB")
        
        if duration > 0:
            mb_per_sec = total_mb / duration
            rps = self.results["requests_sent"] / duration
            print(f"📈 Throughput de dados: {mb_per_sec:.2f} MB/s")
            print(f"🌐 Requests por segundo: {rps:,.0f} RPS")
        
        # Meta 50K
        target_50k = 50000
        performance_ratio = (throughput / target_50k) * 100
        
        if throughput >= target_50k:
            print(f"🎯 META 50K ATINGIDA! {performance_ratio:.1f}% da meta")
            print("🏆 SISTEMA NO LIMITE MÁXIMO!")
        else:
            print(f"📈 Progresso: {performance_ratio:.1f}% da meta de 50K msg/s")
            remaining = target_50k - throughput
            print(f"🎯 Faltam {remaining:,.0f} msg/s para atingir 50K")
            
            # Sugestões para atingir 50K
            print(f"\n💡 SUGESTÕES PARA 50K MSG/S:")
            if throughput > 30000:
                print("   • MUITO PRÓXIMO! Ajustar batch size e concorrência")
                print("   • Considerar múltiplas instâncias REST Proxy")
            elif throughput > 20000:
                print("   • Aumentar concorrência para 300-500")
                print("   • Batch size para 1000+")
                print("   • Verificar limitações de CPU/rede")
            else:
                print("   • Verificar recursos do sistema")
                print("   • Aumentar partições para 100+")
                print("   • Considerar hardware mais potente")
        
        # Latência em modo extremo
        if self.results["response_times"]:
            times = self.results["response_times"][-1000:]  # Últimas 1000 para performance
            print(f"\n⚡ LATÊNCIA (últimas 1000 requests):")
            print(f"   Média: {statistics.mean(times):.2f}ms")
            if len(times) >= 10:
                sorted_times = sorted(times)
                p95 = sorted_times[int(0.95 * len(sorted_times))]
                print(f"   P95: {p95:.2f}ms")
        
        # Análise de erros
        if self.results["errors_by_type"]:
            print(f"\n❌ ERROS DETECTADOS:")
            for error_type, count in self.results["errors_by_type"].items():
                print(f"   {error_type}: {count:,}")
        
        print("=" * 72)

def main():
    parser = argparse.ArgumentParser(description='Teste EXTREMO para 50K+ msg/s')
    parser.add_argument('--messages', type=int, default=50000, help='Número total de mensagens (padrão: 50K)')
    parser.add_argument('--concurrency', type=int, default=200, help='Concorrência extrema (padrão: 200)')
    parser.add_argument('--topic', type=str, default='extreme-performance', help='Nome do tópico')
    parser.add_argument('--batch-size', type=int, default=500, help='Batch size extremo (padrão: 500)')
    parser.add_argument('--url', type=str, default='http://localhost:8082', help='URL do REST Proxy')
    
    args = parser.parse_args()
    
    print(f"🔥 CONFIGURAÇÕES EXTREMAS:")
    print(f"   Mensagens: {args.messages:,}")
    print(f"   Concorrência: {args.concurrency}")
    print(f"   Batch size: {args.batch_size}")
    print(f"   Target: 50,000+ msg/s")
    
    tester = ExtremePerformanceKafkaLoadTester(args.url)
    
    try:
        asyncio.run(tester.run_extreme_test(
            args.topic,
            args.messages,
            args.concurrency,
            args.batch_size
        ))
    except KeyboardInterrupt:
        print("\n\n⏹️ Teste extremo interrompido")

if __name__ == "__main__":
    main()
