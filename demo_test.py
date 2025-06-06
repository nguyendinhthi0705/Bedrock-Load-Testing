#!/usr/bin/env python3
"""
Demo script để test cơ bản Bedrock load testing với Inference Profiles
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
    """Demo test cho Foundation Model với inference profiles"""
    logger.info("Starting demo Foundation Model test với inference profiles...")
    
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
    
    # Test với Claude 3.5 Haiku (cost-effective model) - sử dụng inference profile
    model_name = "claude_3_5_haiku"  # Sử dụng tên từ config
    
    try:
        # Kiểm tra model có sẵn không
        available_models = client.list_available_models()
        if model_name not in available_models:
            logger.error(f"Model {model_name} not found in configuration")
            logger.info(f"Available models: {available_models}")
            return
        
        model_info = client.get_model_info(model_name)
        logger.info(f"Testing with {model_info.get('display_name', model_name)}")
        logger.info(f"Model ID: {model_info.get('model_id')}")
        
        for i, prompt in enumerate(test_prompts):
            logger.info(f"Testing prompt {i+1}/{len(test_prompts)}")
            
            try:
                # Make request using the new method
                result = client.invoke_model_by_name(model_name, prompt)
                
                # Record metrics
                metrics.record_request(
                    request_type="demo_foundation_model",
                    latency=result['latency'],
                    success=True,
                    tokens_input=result['token_usage']['input_tokens'],
                    tokens_output=result['token_usage']['output_tokens'],
                    cost=result['cost']['total_cost']
                )
                
                logger.info(f"✅ Request {i+1} successful")
                logger.info(f"   Latency: {result['latency']:.3f}s")
                logger.info(f"   Input tokens: {result['token_usage']['input_tokens']}")
                logger.info(f"   Output tokens: {result['token_usage']['output_tokens']}")
                logger.info(f"   Cost: ${result['cost']['total_cost']:.6f}")
                logger.info(f"   Response: {result['response_text'][:100]}...")
                
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
            print(f"Average Latency: {overall.get('avg_latency', 0):.3f}s")
        
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

def demo_multiple_models_test():
    """Demo test với nhiều models khác nhau"""
    logger.info("Starting demo test với multiple models...")
    
    client = BedrockClient(region="us-east-1")
    
    # Test với các models khác nhau
    test_models = [
        "claude_3_5_haiku",    # Rẻ nhất
        "nova_lite",           # Nova model
        "claude_3_5_sonnet_v2" # Mạnh nhất
    ]
    
    test_prompt = "Hello! Please introduce yourself briefly."
    
    print("\n" + "="*60)
    print("MULTIPLE MODELS COMPARISON TEST")
    print("="*60)
    
    for model_name in test_models:
        try:
            model_info = client.get_model_info(model_name)
            if not model_info:
                logger.warning(f"Model {model_name} not found in configuration")
                continue
            
            print(f"\n--- Testing {model_info.get('display_name', model_name)} ---")
            
            start_time = time.time()
            result = client.invoke_model_by_name(model_name, test_prompt)
            
            print(f"✅ Success!")
            print(f"   Latency: {result['latency']:.3f}s")
            print(f"   Input tokens: {result['token_usage']['input_tokens']}")
            print(f"   Output tokens: {result['token_usage']['output_tokens']}")
            print(f"   Cost: ${result['cost']['total_cost']:.6f}")
            print(f"   Response: {result['response_text'][:150]}...")
            
        except Exception as e:
            print(f"❌ {model_name} failed: {e}")
        
        time.sleep(1)  # Small delay between models

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

def check_inference_profiles():
    """Kiểm tra inference profiles có sẵn"""
    try:
        client = BedrockClient(region="us-east-1")
        available_models = client.list_available_models()
        
        print("✅ Available models in configuration:")
        for model_name in available_models:
            model_info = client.get_model_info(model_name)
            print(f"  - {model_name}: {model_info.get('display_name', 'N/A')} ({model_info.get('model_id', 'N/A')})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking models: {e}")
        return False

def main():
    print("Amazon Bedrock Load Testing Demo với Inference Profiles")
    print("="*60)
    
    # Check prerequisites
    if not check_aws_credentials():
        sys.exit(1)
    
    if not check_inference_profiles():
        sys.exit(1)
    
    print("\nDemo options:")
    print("1. Basic test với Claude 3.5 Haiku (3 requests)")
    print("2. Multiple models comparison test")
    print("3. Both tests")
    
    choice = input("\nSelect option (1/2/3): ").strip()
    
    if choice == "1":
        print("\nStarting basic demo test...")
        print("This will make 3 requests to Claude 3.5 Haiku")
        print("Estimated cost: ~$0.01")
        
        response = input("\nContinue? (y/N): ")
        if response.lower() != 'y':
            print("Demo cancelled.")
            sys.exit(0)
        
        demo_foundation_model_test()
    
    elif choice == "2":
        print("\nStarting multiple models comparison test...")
        print("This will test 3 different models")
        print("Estimated cost: ~$0.05")
        
        response = input("\nContinue? (y/N): ")
        if response.lower() != 'y':
            print("Demo cancelled.")
            sys.exit(0)
        
        demo_multiple_models_test()
    
    elif choice == "3":
        print("\nStarting both tests...")
        print("Estimated total cost: ~$0.06")
        
        response = input("\nContinue? (y/N): ")
        if response.lower() != 'y':
            print("Demo cancelled.")
            sys.exit(0)
        
        demo_foundation_model_test()
        demo_multiple_models_test()
    
    else:
        print("Invalid choice. Exiting.")
        sys.exit(1)
    
    print("\n✅ Demo completed successfully!")
    print("Check the reports/ directory for detailed results.")

if __name__ == "__main__":
    main()
