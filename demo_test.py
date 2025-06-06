#!/usr/bin/env python3
"""
Demo script để test cơ bản Bedrock load testing
"""

import os
import sys
import time
import json
import logging
from utils.bedrock_client import BedrockClient
from utils.metrics_collector import MetricsCollector

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def demo_foundation_model_test():
    """Demo test cho Foundation Model"""
    logger.info("Starting demo Foundation Model test...")
    
    # Initialize client và metrics
    client = BedrockClient(region="us-east-1")
    metrics = MetricsCollector()
    
    # Start monitoring
    metrics.start_monitoring()
    
    # Test prompts
    test_prompts = [
        "What is artificial intelligence?",
        "Explain cloud computing in simple terms.",
        "Write a Python function to calculate fibonacci numbers."
    ]
    
    # Test với Claude 3.5 Haiku (cost-effective model)
    model_id = "anthropic.claude-3-5-haiku-20241022-v1:0"
    
    try:
        for i, prompt in enumerate(test_prompts):
            logger.info(f"Testing prompt {i+1}/{len(test_prompts)}")
            
            # Prepare request
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "temperature": 0.7,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            try:
                # Make request
                result = client.invoke_model(model_id, request_body)
                
                # Extract response
                response_text = result['response'].get('content', [{}])[0].get('text', '')
                
                # Calculate tokens (rough estimation)
                input_tokens = len(prompt) // 4
                output_tokens = len(response_text) // 4
                cost = (input_tokens / 1000) * 0.0008 + (output_tokens / 1000) * 0.004
                
                # Record metrics
                metrics.record_request(
                    request_type="demo_foundation_model",
                    latency=result['latency'],
                    success=True,
                    tokens_input=input_tokens,
                    tokens_output=output_tokens,
                    cost=cost
                )
                
                logger.info(f"✅ Request {i+1} successful - Latency: {result['latency']:.3f}s, Cost: ${cost:.6f}")
                
            except Exception as e:
                logger.error(f"❌ Request {i+1} failed: {e}")
                metrics.record_request(
                    request_type="demo_foundation_model",
                    latency=0,
                    success=False,
                    error=str(e)
                )
            
            # Small delay between requests
            time.sleep(2)
    
    finally:
        # Stop monitoring
        metrics.stop_monitoring()
        
        # Generate simple report
        performance = metrics.get_performance_summary()
        costs = metrics.get_cost_summary()
        
        print("\n" + "="*50)
        print("DEMO TEST RESULTS")
        print("="*50)
        
        if 'overall' in performance:
            overall = performance['overall']
            print(f"Total Requests: {overall['total_requests']}")
            print(f"Successful Requests: {overall['successful_requests']}")
            print(f"Success Rate: {overall['success_rate']:.2%}")
            print(f"Average RPS: {overall['requests_per_second']:.2f}")
        
        print(f"Total Cost: ${costs['costs'].get('total', 0):.6f}")
        
        # Save results
        os.makedirs('reports', exist_ok=True)
        report_file = f"reports/demo_test_{int(time.time())}.json"
        
        with open(report_file, 'w') as f:
            json.dump({
                'performance': performance,
                'costs': costs,
                'raw_data': metrics.export_raw_data()
            }, f, indent=2)
        
        print(f"Report saved to: {report_file}")

def check_aws_credentials():
    """Kiểm tra AWS credentials"""
    try:
        import boto3
        session = boto3.Session()
        credentials = session.get_credentials()
        
        if credentials is None:
            print("❌ AWS credentials not found!")
            print("Please configure AWS credentials using:")
            print("  aws configure")
            print("  or set environment variables AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
            return False
        
        print("✅ AWS credentials found")
        
        # Test Bedrock access
        bedrock = session.client('bedrock', region_name='us-east-1')
        try:
            bedrock.list_foundation_models()
            print("✅ Bedrock access confirmed")
            return True
        except Exception as e:
            print(f"❌ Bedrock access failed: {e}")
            print("Please ensure you have Bedrock permissions in us-east-1 region")
            return False
            
    except Exception as e:
        print(f"❌ Error checking credentials: {e}")
        return False

def main():
    print("Amazon Bedrock Load Testing Demo")
    print("="*40)
    
    # Check prerequisites
    if not check_aws_credentials():
        sys.exit(1)
    
    print("\nStarting demo test...")
    print("This will make 3 requests to Claude 3.5 Haiku")
    print("Estimated cost: ~$0.01")
    
    response = input("\nContinue? (y/N): ")
    if response.lower() != 'y':
        print("Demo cancelled.")
        sys.exit(0)
    
    # Run demo test
    demo_foundation_model_test()
    
    print("\n✅ Demo completed successfully!")
    print("Check the reports/ directory for detailed results.")

if __name__ == "__main__":
    main()
