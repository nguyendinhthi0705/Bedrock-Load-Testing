#!/usr/bin/env python3
"""
Foundation Model Load Testing Script
Test throughput, latency và cost của các foundation models
"""

import asyncio
import json
import logging
import time
import uuid
import yaml
import argparse
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.bedrock_client import BedrockClient, AsyncBedrockClient
from utils.metrics_collector import MetricsCollector

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FoundationModelLoadTest:
    """Load test cho Foundation Models"""
    
    def __init__(self, config_path: str = "config/test_config.yaml", 
                 models_config_path: str = "config/models_config.yaml"):
        """
        Initialize load test
        
        Args:
            config_path: Path to test configuration
            models_config_path: Path to models configuration
        """
        # Load configurations
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
        with open(models_config_path, 'r') as f:
            self.models_config = yaml.safe_load(f)
        
        # Initialize clients
        self.bedrock_client = BedrockClient(
            region=self.config['aws']['region'],
            profile=self.config['aws'].get('profile')
        )
        
        self.async_client = AsyncBedrockClient(
            region=self.config['aws']['region'],
            profile=self.config['aws'].get('profile')
        )
        
        # Initialize metrics collector
        self.metrics = MetricsCollector(region=self.config['aws']['region'])
        
        # Load test prompts
        self.test_prompts = self._load_test_prompts()
        
    def _load_test_prompts(self) -> List[Dict[str, Any]]:
        """Load test prompts từ file hoặc tạo default prompts"""
        try:
            with open('data/test_prompts.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Test prompts file not found, using default prompts")
            return self._create_default_prompts()
    
    def _create_default_prompts(self) -> List[Dict[str, Any]]:
        """Tạo default test prompts với độ dài khác nhau"""
        prompts = [
            {
                "name": "short_prompt",
                "text": "What is artificial intelligence?",
                "expected_tokens": 50
            },
            {
                "name": "medium_prompt", 
                "text": "Explain the concept of machine learning and how it differs from traditional programming. Include examples of common algorithms and their applications in real-world scenarios.",
                "expected_tokens": 200
            },
            {
                "name": "long_prompt",
                "text": """Write a comprehensive analysis of cloud computing technologies, covering the following aspects:
                1. Infrastructure as a Service (IaaS) - definition, benefits, and major providers
                2. Platform as a Service (PaaS) - use cases and comparison with IaaS
                3. Software as a Service (SaaS) - examples and business models
                4. Serverless computing - advantages and limitations
                5. Multi-cloud strategies and their implementation challenges
                6. Security considerations in cloud environments
                7. Cost optimization techniques for cloud resources
                8. Future trends in cloud computing including edge computing and quantum computing integration
                
                Please provide detailed explanations with practical examples and industry best practices.""",
                "expected_tokens": 800
            },
            {
                "name": "code_generation",
                "text": "Write a Python function that implements a binary search algorithm. Include error handling, documentation, and unit tests.",
                "expected_tokens": 300
            },
            {
                "name": "creative_writing",
                "text": "Write a short story about a robot that discovers emotions. The story should be engaging, have a clear beginning, middle, and end, and explore themes of consciousness and humanity.",
                "expected_tokens": 500
            }
        ]
        return prompts
    
    def _count_tokens(self, text: str) -> int:
        """Ước tính số tokens (rough estimation)"""
        # Simple estimation: ~4 characters per token for English
        return len(text) // 4
    
    def _calculate_cost(self, model_config: Dict, input_tokens: int, output_tokens: int) -> float:
        """Tính cost cho request"""
        pricing = model_config.get('pricing', {})
        input_cost = (input_tokens / 1000) * pricing.get('input_tokens', 0)
        output_cost = (output_tokens / 1000) * pricing.get('output_tokens', 0)
        return input_cost + output_cost
    
    def _prepare_request_body(self, model_id: str, prompt: str, model_config: Dict) -> Dict[str, Any]:
        """Chuẩn bị request body cho model"""
        if "anthropic.claude" in model_id:
            return {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": model_config.get('max_tokens', 4096),
                "temperature": model_config.get('temperature', 0.7),
                "top_p": model_config.get('top_p', 0.9),
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
        elif "amazon.titan" in model_id:
            return {
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": model_config.get('max_tokens', 4096),
                    "temperature": model_config.get('temperature', 0.7),
                    "topP": model_config.get('top_p', 0.9)
                }
            }
        elif "meta.llama" in model_id:
            return {
                "prompt": prompt,
                "max_gen_len": model_config.get('max_tokens', 4096),
                "temperature": model_config.get('temperature', 0.7),
                "top_p": model_config.get('top_p', 0.9)
            }
        else:
            # Generic format
            return {
                "prompt": prompt,
                "max_tokens": model_config.get('max_tokens', 4096),
                "temperature": model_config.get('temperature', 0.7)
            }
    
    def _extract_response_text(self, model_id: str, response: Dict) -> str:
        """Extract text từ model response"""
        if "anthropic.claude" in model_id:
            return response.get('content', [{}])[0].get('text', '')
        elif "amazon.titan" in model_id:
            return response.get('results', [{}])[0].get('outputText', '')
        elif "meta.llama" in model_id:
            return response.get('generation', '')
        else:
            return str(response)
    
    def single_request_test(self, model_name: str, prompt_data: Dict) -> Dict[str, Any]:
        """Test một request đơn lẻ"""
        model_config = self.models_config['foundation_models'][model_name]
        model_id = model_config['model_id']
        
        # Prepare request
        request_body = self._prepare_request_body(model_id, prompt_data['text'], model_config)
        
        try:
            # Make request
            result = self.bedrock_client.invoke_model(model_id, request_body)
            
            # Extract response
            response_text = self._extract_response_text(model_id, result['response'])
            
            # Calculate tokens and cost
            input_tokens = self._count_tokens(prompt_data['text'])
            output_tokens = self._count_tokens(response_text)
            cost = self._calculate_cost(model_config, input_tokens, output_tokens)
            
            # Record metrics
            self.metrics.record_request(
                request_type=f"foundation_model_{model_name}",
                latency=result['latency'],
                success=True,
                tokens_input=input_tokens,
                tokens_output=output_tokens,
                cost=cost
            )
            
            return {
                'success': True,
                'latency': result['latency'],
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'cost': cost,
                'response_length': len(response_text)
            }
            
        except Exception as e:
            logger.error(f"Error in single request: {e}")
            
            self.metrics.record_request(
                request_type=f"foundation_model_{model_name}",
                latency=0,
                success=False,
                error=str(e)
            )
            
            return {
                'success': False,
                'error': str(e)
            }
    
    async def async_request_test(self, model_name: str, prompt_data: Dict) -> Dict[str, Any]:
        """Async version của single request test"""
        model_config = self.models_config['foundation_models'][model_name]
        model_id = model_config['model_id']
        
        request_body = self._prepare_request_body(model_id, prompt_data['text'], model_config)
        
        try:
            result = await self.async_client.invoke_model_async(model_id, request_body)
            
            response_text = self._extract_response_text(model_id, result['response'])
            input_tokens = self._count_tokens(prompt_data['text'])
            output_tokens = self._count_tokens(response_text)
            cost = self._calculate_cost(model_config, input_tokens, output_tokens)
            
            self.metrics.record_request(
                request_type=f"foundation_model_{model_name}",
                latency=result['latency'],
                success=True,
                tokens_input=input_tokens,
                tokens_output=output_tokens,
                cost=cost
            )
            
            return {
                'success': True,
                'latency': result['latency'],
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'cost': cost
            }
            
        except Exception as e:
            self.metrics.record_request(
                request_type=f"foundation_model_{model_name}",
                latency=0,
                success=False,
                error=str(e)
            )
            
            return {'success': False, 'error': str(e)}
    
    def concurrent_test(self, model_name: str, concurrent_users: int, 
                       test_duration: int) -> Dict[str, Any]:
        """Test với concurrent users"""
        logger.info(f"Starting concurrent test: {model_name}, {concurrent_users} users, {test_duration}s")
        
        results = []
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            
            # Submit initial requests
            for _ in range(concurrent_users):
                prompt = self.test_prompts[len(futures) % len(self.test_prompts)]
                future = executor.submit(self.single_request_test, model_name, prompt)
                futures.append(future)
            
            # Keep submitting requests until test duration is reached
            while time.time() - start_time < test_duration:
                # Check for completed requests
                completed_futures = []
                for future in futures:
                    if future.done():
                        try:
                            result = future.result()
                            results.append(result)
                        except Exception as e:
                            logger.error(f"Future error: {e}")
                        completed_futures.append(future)
                
                # Remove completed futures and submit new ones
                for future in completed_futures:
                    futures.remove(future)
                    
                    # Submit new request if still within test duration
                    if time.time() - start_time < test_duration:
                        prompt = self.test_prompts[len(results) % len(self.test_prompts)]
                        new_future = executor.submit(self.single_request_test, model_name, prompt)
                        futures.append(new_future)
                
                time.sleep(0.1)  # Small delay to prevent busy waiting
            
            # Wait for remaining futures to complete
            for future in as_completed(futures, timeout=30):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Final future error: {e}")
        
        return {
            'total_requests': len(results),
            'successful_requests': sum(1 for r in results if r.get('success')),
            'test_duration': time.time() - start_time
        }
    
    async def async_concurrent_test(self, model_name: str, concurrent_users: int, 
                                  test_duration: int) -> Dict[str, Any]:
        """Async concurrent test"""
        logger.info(f"Starting async concurrent test: {model_name}, {concurrent_users} users")
        
        results = []
        start_time = time.time()
        
        async def worker():
            while time.time() - start_time < test_duration:
                prompt = self.test_prompts[len(results) % len(self.test_prompts)]
                result = await self.async_request_test(model_name, prompt)
                results.append(result)
                await asyncio.sleep(0.1)
        
        # Create worker tasks
        tasks = [asyncio.create_task(worker()) for _ in range(concurrent_users)]
        
        # Wait for all tasks to complete or timeout
        try:
            await asyncio.wait_for(asyncio.gather(*tasks), timeout=test_duration + 30)
        except asyncio.TimeoutError:
            logger.warning("Async test timed out")
            for task in tasks:
                task.cancel()
        
        return {
            'total_requests': len(results),
            'successful_requests': sum(1 for r in results if r.get('success')),
            'test_duration': time.time() - start_time
        }
    
    def run_comprehensive_test(self, models_to_test: Optional[List[str]] = None):
        """Chạy comprehensive test cho tất cả models"""
        if models_to_test is None:
            models_to_test = list(self.models_config['foundation_models'].keys())
        
        logger.info(f"Starting comprehensive test for models: {models_to_test}")
        
        # Start metrics collection
        self.metrics.start_monitoring()
        
        try:
            for model_name in models_to_test:
                logger.info(f"Testing model: {model_name}")
                
                # Test với các mức concurrent users khác nhau
                for concurrent_users in self.config['load_test']['concurrent_users']:
                    logger.info(f"Testing {concurrent_users} concurrent users")
                    
                    # Concurrent test
                    result = self.concurrent_test(
                        model_name, 
                        concurrent_users, 
                        self.config['load_test']['test_duration']
                    )
                    
                    logger.info(f"Completed: {result['successful_requests']}/{result['total_requests']} requests")
                    
                    # Small break between tests
                    time.sleep(10)
        
        finally:
            # Stop metrics collection
            self.metrics.stop_monitoring()
            
            # Generate report
            self._generate_report()
    
    def _generate_report(self):
        """Tạo báo cáo kết quả test"""
        logger.info("Generating test report...")
        
        # Get metrics summaries
        performance_summary = self.metrics.get_performance_summary()
        cost_summary = self.metrics.get_cost_summary()
        error_summary = self.metrics.get_error_summary()
        system_summary = self.metrics.get_system_metrics_summary()
        
        # Create report
        report = {
            'test_info': {
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'test_type': 'Foundation Model Load Test',
                'configuration': self.config
            },
            'performance': performance_summary,
            'costs': cost_summary,
            'errors': error_summary,
            'system_metrics': system_summary,
            'raw_data': self.metrics.export_raw_data()
        }
        
        # Save report
        os.makedirs('reports', exist_ok=True)
        report_file = f"reports/foundation_model_test_{int(time.time())}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report saved to: {report_file}")
        
        # Print summary
        self._print_summary(performance_summary, cost_summary)
    
    def _print_summary(self, performance: Dict, costs: Dict):
        """In tóm tắt kết quả"""
        print("\n" + "="*60)
        print("FOUNDATION MODEL LOAD TEST SUMMARY")
        print("="*60)
        
        if 'overall' in performance:
            overall = performance['overall']
            print(f"Total Requests: {overall['total_requests']}")
            print(f"Success Rate: {overall['success_rate']:.2%}")
            print(f"Requests/Second: {overall['requests_per_second']:.2f}")
            print(f"Test Duration: {overall['test_duration']:.2f}s")
        
        print(f"\nTotal Cost: ${costs['costs'].get('total', 0):.4f}")
        
        print("\nPer-Model Performance:")
        for key, metrics in performance.items():
            if key != 'overall' and isinstance(metrics, dict):
                print(f"\n{key}:")
                print(f"  Success Rate: {metrics['success_rate']:.2%}")
                print(f"  Avg Latency: {metrics['avg_latency']:.3f}s")
                print(f"  P95 Latency: {metrics['p95_latency']:.3f}s")
                print(f"  P99 Latency: {metrics['p99_latency']:.3f}s")

def main():
    parser = argparse.ArgumentParser(description='Foundation Model Load Test')
    parser.add_argument('--models', nargs='+', help='Models to test')
    parser.add_argument('--config', default='config/test_config.yaml', help='Test config file')
    parser.add_argument('--models-config', default='config/models_config.yaml', help='Models config file')
    
    args = parser.parse_args()
    
    # Initialize and run test
    test = FoundationModelLoadTest(args.config, args.models_config)
    test.run_comprehensive_test(args.models)

if __name__ == "__main__":
    main()
