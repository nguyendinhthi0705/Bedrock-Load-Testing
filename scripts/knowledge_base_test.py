#!/usr/bin/env python3
"""
Knowledge Base Load Testing Script
Test performance của Bedrock Knowledge Bases
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

class KnowledgeBaseLoadTest:
    """Load test cho Bedrock Knowledge Bases"""
    
    def __init__(self, config_path: str = "config/test_config.yaml", 
                 models_config_path: str = "config/models_config.yaml"):
        """
        Initialize Knowledge Base load test
        
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
        
        # Knowledge Base configuration
        self.kb_config = self.models_config.get('knowledge_base', {})
        self.kb_id = self.kb_config.get('kb_id')
        
        if not self.kb_id:
            raise ValueError("Knowledge Base ID not configured. Please update models_config.yaml")
        
        # Load test queries
        self.test_queries = self._load_test_queries()
        
    def _load_test_queries(self) -> List[Dict[str, Any]]:
        """Load test queries từ file hoặc tạo default queries"""
        try:
            with open('data/knowledge_base_queries.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Knowledge base queries file not found, using default queries")
            return self._create_default_queries()
    
    def _create_default_queries(self) -> List[Dict[str, Any]]:
        """Tạo default test queries"""
        queries = [
            {
                "name": "simple_factual",
                "text": "What is the main purpose of this service?",
                "category": "factual",
                "expected_results": 5
            },
            {
                "name": "complex_analytical",
                "text": "Compare the advantages and disadvantages of different approaches mentioned in the documentation. Provide specific examples and use cases.",
                "category": "analytical",
                "expected_results": 10
            },
            {
                "name": "technical_details",
                "text": "What are the technical requirements and specifications for implementation?",
                "category": "technical",
                "expected_results": 8
            },
            {
                "name": "troubleshooting",
                "text": "How do I resolve common errors and issues that might occur during setup?",
                "category": "troubleshooting",
                "expected_results": 7
            },
            {
                "name": "best_practices",
                "text": "What are the recommended best practices and optimization techniques?",
                "category": "best_practices",
                "expected_results": 6
            },
            {
                "name": "integration",
                "text": "How does this integrate with other AWS services and third-party tools?",
                "category": "integration",
                "expected_results": 8
            },
            {
                "name": "cost_optimization",
                "text": "What are the cost considerations and how can I optimize expenses?",
                "category": "cost",
                "expected_results": 5
            },
            {
                "name": "security",
                "text": "What security measures and compliance requirements should I be aware of?",
                "category": "security",
                "expected_results": 9
            },
            {
                "name": "performance",
                "text": "How can I monitor and improve performance metrics?",
                "category": "performance",
                "expected_results": 6
            },
            {
                "name": "scalability",
                "text": "What are the scalability options and limitations I should consider?",
                "category": "scalability",
                "expected_results": 7
            }
        ]
        return queries
    
    def _count_tokens(self, text: str) -> int:
        """Ước tính số tokens"""
        return len(text) // 4
    
    def _calculate_kb_cost(self, input_tokens: int, output_tokens: int, 
                          num_citations: int = 0) -> float:
        """
        Tính cost cho Knowledge Base query
        
        Args:
            input_tokens: Input tokens
            output_tokens: Output tokens  
            num_citations: Số citations trả về
            
        Returns:
            Estimated cost
        """
        # Foundation model cost (sử dụng Claude 3 Haiku làm default)
        model_cost = (input_tokens / 1000) * 0.0008 + (output_tokens / 1000) * 0.004
        
        # OCU cost (ước tính dựa trên query complexity)
        # Giả sử mỗi query sử dụng ~0.001 OCU-hour
        ocu_cost = 0.001 * 0.20  # $0.20 per OCU-hour
        
        return model_cost + ocu_cost
    
    def single_kb_query(self, query_data: Dict) -> Dict[str, Any]:
        """Test một Knowledge Base query đơn lẻ"""
        query_text = query_data['text']
        
        try:
            # Prepare retrieval config
            retrieval_config = self.kb_config.get('retrieval_config', {})
            generation_config = self.kb_config.get('generation_config', {})
            
            # Make request
            result = self.bedrock_client.retrieve_and_generate(
                kb_id=self.kb_id,
                query=query_text,
                retrieval_config=retrieval_config,
                generation_config=generation_config
            )
            
            # Extract response details
            response_text = result['response'].get('output', {}).get('text', '')
            citations = result.get('citations', [])
            session_id = result.get('session_id', '')
            
            # Calculate tokens and cost
            input_tokens = self._count_tokens(query_text)
            output_tokens = self._count_tokens(response_text)
            cost = self._calculate_kb_cost(input_tokens, output_tokens, len(citations))
            
            # Record metrics
            self.metrics.record_request(
                request_type="knowledge_base",
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
                'response_length': len(response_text),
                'num_citations': len(citations),
                'session_id': session_id,
                'query_category': query_data.get('category', 'unknown')
            }
            
        except Exception as e:
            logger.error(f"Error in KB query: {e}")
            
            self.metrics.record_request(
                request_type="knowledge_base",
                latency=0,
                success=False,
                error=str(e)
            )
            
            return {
                'success': False,
                'error': str(e),
                'query_category': query_data.get('category', 'unknown')
            }
    
    async def async_kb_query(self, query_data: Dict) -> Dict[str, Any]:
        """Async version của KB query"""
        query_text = query_data['text']
        
        try:
            result = await self.async_client.retrieve_and_generate_async(
                kb_id=self.kb_id,
                query=query_text
            )
            
            response_text = result['response'].get('output', {}).get('text', '')
            citations = result.get('citations', [])
            
            input_tokens = self._count_tokens(query_text)
            output_tokens = self._count_tokens(response_text)
            cost = self._calculate_kb_cost(input_tokens, output_tokens, len(citations))
            
            self.metrics.record_request(
                request_type="knowledge_base",
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
                'num_citations': len(citations),
                'query_category': query_data.get('category', 'unknown')
            }
            
        except Exception as e:
            self.metrics.record_request(
                request_type="knowledge_base",
                latency=0,
                success=False,
                error=str(e)
            )
            
            return {
                'success': False,
                'error': str(e),
                'query_category': query_data.get('category', 'unknown')
            }
    
    def concurrent_kb_test(self, concurrent_users: int, test_duration: int) -> Dict[str, Any]:
        """Test KB với concurrent users"""
        logger.info(f"Starting concurrent KB test: {concurrent_users} users, {test_duration}s")
        
        results = []
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            
            # Submit initial requests
            for _ in range(concurrent_users):
                query = self.test_queries[len(futures) % len(self.test_queries)]
                future = executor.submit(self.single_kb_query, query)
                futures.append(future)
            
            # Keep submitting requests until test duration is reached
            while time.time() - start_time < test_duration:
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
                    
                    if time.time() - start_time < test_duration:
                        query = self.test_queries[len(results) % len(self.test_queries)]
                        new_future = executor.submit(self.single_kb_query, query)
                        futures.append(new_future)
                
                time.sleep(0.1)
            
            # Wait for remaining futures
            for future in as_completed(futures, timeout=30):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Final future error: {e}")
        
        return {
            'total_requests': len(results),
            'successful_requests': sum(1 for r in results if r.get('success')),
            'test_duration': time.time() - start_time,
            'results': results
        }
    
    def query_pattern_test(self) -> Dict[str, Any]:
        """Test các pattern query khác nhau"""
        logger.info("Starting query pattern test")
        
        pattern_results = {}
        
        # Group queries by category
        queries_by_category = {}
        for query in self.test_queries:
            category = query.get('category', 'unknown')
            if category not in queries_by_category:
                queries_by_category[category] = []
            queries_by_category[category].append(query)
        
        # Test each category
        for category, queries in queries_by_category.items():
            logger.info(f"Testing category: {category}")
            category_results = []
            
            for query in queries:
                result = self.single_kb_query(query)
                category_results.append(result)
                time.sleep(1)  # Small delay between queries
            
            pattern_results[category] = {
                'total_queries': len(category_results),
                'successful_queries': sum(1 for r in category_results if r.get('success')),
                'avg_latency': sum(r.get('latency', 0) for r in category_results if r.get('success')) / max(1, sum(1 for r in category_results if r.get('success'))),
                'avg_citations': sum(r.get('num_citations', 0) for r in category_results if r.get('success')) / max(1, sum(1 for r in category_results if r.get('success'))),
                'total_cost': sum(r.get('cost', 0) for r in category_results),
                'results': category_results
            }
        
        return pattern_results
    
    def session_continuity_test(self, num_queries: int = 10) -> Dict[str, Any]:
        """Test session continuity với multiple queries"""
        logger.info(f"Starting session continuity test with {num_queries} queries")
        
        session_id = None
        results = []
        
        for i in range(num_queries):
            query = self.test_queries[i % len(self.test_queries)]
            
            try:
                # Use existing session if available
                if session_id:
                    # Note: Bedrock KB doesn't directly support session continuation in retrieve_and_generate
                    # This is more applicable to Agent conversations
                    pass
                
                result = self.single_kb_query(query)
                
                if result.get('success') and result.get('session_id'):
                    session_id = result['session_id']
                
                results.append({
                    'query_index': i,
                    'query_category': query.get('category'),
                    'result': result
                })
                
                time.sleep(2)  # Delay between queries in session
                
            except Exception as e:
                logger.error(f"Error in session query {i}: {e}")
                results.append({
                    'query_index': i,
                    'error': str(e)
                })
        
        return {
            'total_queries': len(results),
            'successful_queries': sum(1 for r in results if r.get('result', {}).get('success')),
            'session_id': session_id,
            'results': results
        }
    
    def run_comprehensive_test(self):
        """Chạy comprehensive test cho Knowledge Base"""
        logger.info("Starting comprehensive Knowledge Base test")
        
        # Start metrics collection
        self.metrics.start_monitoring()
        
        test_results = {}
        
        try:
            # 1. Query pattern test
            logger.info("Running query pattern test...")
            test_results['query_patterns'] = self.query_pattern_test()
            
            # 2. Session continuity test
            logger.info("Running session continuity test...")
            test_results['session_continuity'] = self.session_continuity_test()
            
            # 3. Concurrent user tests
            logger.info("Running concurrent user tests...")
            concurrent_results = {}
            
            for concurrent_users in self.config['load_test']['concurrent_users']:
                if concurrent_users > 20:  # Limit concurrent users for KB to avoid throttling
                    continue
                    
                logger.info(f"Testing {concurrent_users} concurrent users")
                
                result = self.concurrent_kb_test(
                    concurrent_users, 
                    self.config['load_test']['test_duration']
                )
                
                concurrent_results[f"{concurrent_users}_users"] = result
                
                logger.info(f"Completed: {result['successful_requests']}/{result['total_requests']} requests")
                
                # Break between tests
                time.sleep(15)
            
            test_results['concurrent_tests'] = concurrent_results
            
        finally:
            # Stop metrics collection
            self.metrics.stop_monitoring()
            
            # Generate report
            self._generate_report(test_results)
    
    def _generate_report(self, test_results: Dict):
        """Tạo báo cáo kết quả test"""
        logger.info("Generating Knowledge Base test report...")
        
        # Get metrics summaries
        performance_summary = self.metrics.get_performance_summary()
        cost_summary = self.metrics.get_cost_summary()
        error_summary = self.metrics.get_error_summary()
        system_summary = self.metrics.get_system_metrics_summary()
        
        # Create comprehensive report
        report = {
            'test_info': {
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'test_type': 'Knowledge Base Load Test',
                'knowledge_base_id': self.kb_id,
                'configuration': self.config
            },
            'test_results': test_results,
            'performance': performance_summary,
            'costs': cost_summary,
            'errors': error_summary,
            'system_metrics': system_summary,
            'raw_data': self.metrics.export_raw_data()
        }
        
        # Save report
        os.makedirs('reports', exist_ok=True)
        report_file = f"reports/knowledge_base_test_{int(time.time())}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report saved to: {report_file}")
        
        # Print summary
        self._print_summary(performance_summary, cost_summary, test_results)
    
    def _print_summary(self, performance: Dict, costs: Dict, test_results: Dict):
        """In tóm tắt kết quả"""
        print("\n" + "="*60)
        print("KNOWLEDGE BASE LOAD TEST SUMMARY")
        print("="*60)
        
        if 'overall' in performance:
            overall = performance['overall']
            print(f"Total Requests: {overall['total_requests']}")
            print(f"Success Rate: {overall['success_rate']:.2%}")
            print(f"Requests/Second: {overall['requests_per_second']:.2f}")
            print(f"Test Duration: {overall['test_duration']:.2f}s")
        
        print(f"\nTotal Cost: ${costs['costs'].get('total', 0):.4f}")
        
        # KB specific metrics
        if 'knowledge_base' in performance:
            kb_metrics = performance['knowledge_base']
            print(f"\nKnowledge Base Performance:")
            print(f"  Success Rate: {kb_metrics['success_rate']:.2%}")
            print(f"  Avg Latency: {kb_metrics['avg_latency']:.3f}s")
            print(f"  P95 Latency: {kb_metrics['p95_latency']:.3f}s")
            print(f"  P99 Latency: {kb_metrics['p99_latency']:.3f}s")
        
        # Query pattern results
        if 'query_patterns' in test_results:
            print(f"\nQuery Pattern Results:")
            for category, results in test_results['query_patterns'].items():
                print(f"  {category}:")
                print(f"    Success Rate: {results['successful_queries']}/{results['total_queries']}")
                print(f"    Avg Latency: {results['avg_latency']:.3f}s")
                print(f"    Avg Citations: {results['avg_citations']:.1f}")
                print(f"    Cost: ${results['total_cost']:.4f}")

def main():
    parser = argparse.ArgumentParser(description='Knowledge Base Load Test')
    parser.add_argument('--config', default='config/test_config.yaml', help='Test config file')
    parser.add_argument('--models-config', default='config/models_config.yaml', help='Models config file')
    parser.add_argument('--kb-id', help='Knowledge Base ID to test')
    
    args = parser.parse_args()
    
    # Initialize test
    test = KnowledgeBaseLoadTest(args.config, args.models_config)
    
    # Override KB ID if provided
    if args.kb_id:
        test.kb_id = args.kb_id
    
    # Run test
    test.run_comprehensive_test()

if __name__ == "__main__":
    main()
