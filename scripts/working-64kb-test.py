#!/usr/bin/env python3
"""
Teste de carga com mensagens de 64KB - Versão Funcional
Baseado no método que funcionou no teste simples
"""

import asyncio
import aiohttp
import time
import json
import base64
import argparse
import statistics
from datetime import datetime

class WorkingLargeMessageTester:
    def __init__(self, rest_proxy_url="http://localhost:8082"):
        self.rest_proxy_url = rest_proxy_url
        self.results = {
            "success_count": 0,
            "error_count": 0,
            "response_times": [],
            "bytes_sent": 0
        }
        
        # Gerar payload base64 de 64KB (método que funcionou)
        self.base64_payload = self.generate_working_64kb_payload()
        print(f"✅ Payload de {len(self.base64_payload)/1024:.2f}KB criado com sucesso")
    
    def generate_working_64kb_payload(self):
        """Gera payload base64 de 64KB usando método que funcionou"""
        # 64KB de base64 = aproximadamente 48KB de dados originais
        target_original_size = 48 * 1024  # 48KB
        
        # Usar padrão que sabemos que funciona
        pattern = "Hello World! This is a test payload for Kafka load testing with 64KB messages. " * 100
        
        # Repetir até atingir o tamanho
        data = ""
        while len(data) < target_original_size:
            data += pattern
        
        # Cortar para tamanho exato
        data = data[:target_original_size]
        
        # Converter para base64
        return base64.b64encode(data.encode('utf-8')).decode('utf-8')
    
    def create_message(self, msg_id, system_name="kafka-load-test"):
        """Cria mensagem no mesmo formato que funcionou"""
        return {
            "records": [
                {
                    "key": f"large-msg-{msg_id}",
                    "value": {
                        "id": msg_id,
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "system": system_name,
                        "payload": self.base64_payload
                    }
                }
            ]
        }
    
    async def send_single_message(self, session, topic, msg_id, system_name):
        """Envia uma única mensagem (método que funcionou)"""
        message = self.create_message(msg_id, system_name)
        
        headers = {
            'Content-Type': 'application/vnd.kafka.json.v2+json',
            'Accept': 'application/vnd.kafka.v2+json'
        }
        
        # Calcular tamanho
        message_json = json.dumps(message)
        message_size = len(message_json.encode('utf-8'))
        self.results["bytes_sent"] += message_size
        
        start_time = time.time()
        
        try:
            async with session.post(
                f"{self.rest_proxy_url}/topics/{topic}",
                json=message,  # Usar json= em vez de data=
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                response_time = (time.time() - start_time) * 1000
                self.results["response_times"].append(response_time)
                
                if response.status == 200:
                    self.results["success_count"] += 1
                    return True, response_time
                else:
                    self.results["error_count"] += 1
                    error_text = await response.text()
                    print(f"❌ Erro {response.status} na mensagem {msg_id}: {error_text[:100]}")
                    return False, response_time
                    
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.results["response_times"].append(response_time)
            self.results["error_count"] += 1
            print(f"❌ Exceção na mensagem {msg_id}: {str(e)[:100]}")
            return False, response_time
    
    async def run_working_test(self, topic, total_messages, concurrency):
        """Executa teste usando método que sabemos que funciona"""
        print("📦 === TESTE DE MENSAGENS 64KB (MÉTODO FUNCIONAL) ===")
        print(f"Tópico: {topic}")
        print(f"Total de mensagens: {total_messages:,}")
        print(f"Concorrência: {concurrency}")
        print(f"Tamanho da mensagem: ~64KB")
        print(f"Volume total estimado: {(total_messages * 64 / 1024):.2f} MB")
        print("=" * 60)
        
        start_time = time.time()
        
        # Configurar session como no teste que funcionou
        async with aiohttp.ClientSession() as session:
            
            # Verificar conectividade
            try:
                async with session.get(f"{self.rest_proxy_url}/topics") as response:
                    if response.status != 200:
                        print(f"❌ ERRO: REST Proxy status {response.status}")
                        return
                print("✅ Conectividade verificada")
            except Exception as e:
                print(f"❌ ERRO de conectividade: {e}")
                return
            
            # Criar semáforo para controlar concorrência
            semaphore = asyncio.Semaphore(concurrency)
            
            # Criar tasks para todas as mensagens
            tasks = []
            for msg_id in range(1, total_messages + 1):
                system_name = f"load-test-{msg_id % concurrency}"
                
                async def send_with_semaphore(msg_id, system_name):
                    async with semaphore:
                        return await self.send_single_message(session, topic, msg_id, system_name)
                
                task = send_with_semaphore(msg_id, system_name)
                tasks.append(task)
            
            print(f"🚀 Enviando {total_messages} mensagens com concorrência {concurrency}...")
            
            # Executar com progresso
            completed = 0
            for task in asyncio.as_completed(tasks):
                await task
                completed += 1
                
                if completed % 10 == 0 or completed == total_messages:
                    progress = (completed / total_messages) * 100
                    elapsed = time.time() - start_time
                    current_throughput = self.results["success_count"] / elapsed if elapsed > 0 else 0
                    
                    print(f"📊 Progresso: {progress:.1f}% | "
                          f"Sucessos: {self.results['success_count']} | "
                          f"Erros: {self.results['error_count']} | "
                          f"Throughput: {current_throughput:.1f} msg/s")
        
        end_time = time.time()
        duration = end_time - start_time
        
        self.print_working_results(duration, total_messages)
    
    def print_working_results(self, duration, total_messages):
        """Imprime resultados do teste funcional"""
        throughput = self.results["success_count"] / duration if duration > 0 else 0
        
        print("\n" + "🎯" + "=" * 60)
        print("RESULTADOS - TESTE FUNCIONAL COM MENSAGENS 64KB")
        print("=" * 62)
        print(f"⏱️  Tempo total: {duration:.3f}s")
        print(f"📤 Mensagens enviadas: {total_messages:,}")
        print(f"✅ Sucessos: {self.results['success_count']:,}")
        print(f"❌ Erros: {self.results['error_count']:,}")
        
        if total_messages > 0:
            success_rate = (self.results['success_count'] / total_messages) * 100
            print(f"📊 Taxa de sucesso: {success_rate:.2f}%")
        
        print(f"🚀 Throughput: {throughput:.2f} msg/s")
        
        # Análise de dados
        total_mb = self.results['bytes_sent'] / 1024 / 1024
        print(f"💾 Volume enviado: {total_mb:.2f} MB")
        
        if duration > 0:
            mb_per_sec = total_mb / duration
            print(f"📈 Throughput de dados: {mb_per_sec:.2f} MB/s")
        
        # Latência
        if self.results["response_times"]:
            times = self.results["response_times"]
            print(f"\n📊 LATÊNCIA:")
            print(f"   Média: {statistics.mean(times):.2f}ms")
            print(f"   Mínima: {min(times):.2f}ms")
            print(f"   Máxima: {max(times):.2f}ms")
            
            if len(times) >= 10:
                sorted_times = sorted(times)
                p95 = sorted_times[int(0.95 * len(sorted_times))]
                print(f"   P95: {p95:.2f}ms")
        
        print("=" * 62)

def main():
    parser = argparse.ArgumentParser(description='Teste funcional com mensagens de 64KB')
    parser.add_argument('--messages', type=int, default=50, help='Número de mensagens')
    parser.add_argument('--concurrency', type=int, default=5, help='Concorrência')
    parser.add_argument('--topic', type=str, default='large-messages', help='Tópico')
    parser.add_argument('--url', type=str, default='http://localhost:8082', help='REST Proxy URL')
    
    args = parser.parse_args()
    
    tester = WorkingLargeMessageTester(args.url)
    
    try:
        asyncio.run(tester.run_working_test(
            args.topic,
            args.messages,
            args.concurrency
        ))
    except KeyboardInterrupt:
        print("\n⏹️ Teste interrompido")

if __name__ == "__main__":
    main()
