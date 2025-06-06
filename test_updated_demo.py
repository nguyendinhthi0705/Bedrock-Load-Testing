#!/usr/bin/env python3
"""
Test script để kiểm tra code đã cập nhật với inference profiles
"""

import os
import sys
import time
import logging
from utils.bedrock_client import BedrockClient

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_single_request():
    """Test một request đơn lẻ"""
    logger.info("Testing single request với inference profile...")
    
    try:
        # Initialize client
        client = BedrockClient(region="us-east-1")
        
        # Test với Claude 3.5 Sonnet v2 - model gây lỗi ban đầu
        model_name = "claude_3_5_sonnet_v2"
        prompt = "Hello! Can you confirm that you're working correctly with inference profiles?"
        
        logger.info(f"Testing model: {model_name}")
        
        # Make request
        result = client.invoke_model_by_name(model_name, prompt)
        
        logger.info("✅ SUCCESS!")
        logger.info(f"   Latency: {result['latency']:.3f}s")
        logger.info(f"   Input tokens: {result['token_usage']['input_tokens']}")
        logger.info(f"   Output tokens: {result['token_usage']['output_tokens']}")
        logger.info(f"   Cost: ${result['cost']['total_cost']:.6f}")
        logger.info(f"   Response: {result['response_text'][:200]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ FAILED: {e}")
        return False

def test_multiple_models():
    """Test nhiều models khác nhau"""
    logger.info("Testing multiple models...")
    
    client = BedrockClient(region="us-east-1")
    
    # Test models
    test_models = [
        "claude_3_5_sonnet_v2",  # Model gây lỗi ban đầu
        "claude_3_5_haiku",      # Model rẻ
        "nova_lite",             # Nova model
        "llama3_2_1b"           # Llama model
    ]
    
    prompt = "What is 2+2? Please answer briefly."
    results = {}
    
    for model_name in test_models:
        try:
            logger.info(f"Testing {model_name}...")
            
            start_time = time.time()
            result = client.invoke_model_by_name(model_name, prompt)
            
            results[model_name] = {
                'success': True,
                'latency': result['latency'],
                'cost': result['cost']['total_cost'],
                'tokens': result['token_usage'],
                'response_preview': result['response_text'][:100]
            }
            
            logger.info(f"✅ {model_name} - SUCCESS (Latency: {result['latency']:.3f}s, Cost: ${result['cost']['total_cost']:.6f})")
            
        except Exception as e:
            logger.error(f"❌ {model_name} - FAILED: {e}")
            results[model_name] = {
                'success': False,
                'error': str(e)
            }
        
        time.sleep(1)  # Small delay
    
    # Summary
    print("\n" + "="*60)
    print("MULTIPLE MODELS TEST SUMMARY")
    print("="*60)
    
    successful = 0
    total_cost = 0
    
    for model_name, result in results.items():
        if result['success']:
            successful += 1
            total_cost += result['cost']
            print(f"✅ {model_name}: {result['latency']:.3f}s, ${result['cost']:.6f}")
        else:
            print(f"❌ {model_name}: {result['error']}")
    
    print(f"\nSuccess Rate: {successful}/{len(test_models)} ({successful/len(test_models)*100:.1f}%)")
    print(f"Total Cost: ${total_cost:.6f}")
    
    return successful == len(test_models)

def main():
    print("Testing Updated Bedrock Code với Inference Profiles")
    print("="*60)
    
    # Test 1: Single request với model gây lỗi ban đầu
    print("\n1. Testing single request với Claude 3.5 Sonnet v2...")
    success1 = test_single_request()
    
    if not success1:
        print("❌ Single request test failed. Stopping.")
        sys.exit(1)
    
    # Test 2: Multiple models
    print("\n2. Testing multiple models...")
    success2 = test_multiple_models()
    
    # Final result
    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)
    
    if success1 and success2:
        print("✅ All tests PASSED!")
        print("🎉 Code đã được cập nhật thành công để sử dụng inference profiles!")
    else:
        print("❌ Some tests FAILED!")
        if not success1:
            print("   - Single request test failed")
        if not success2:
            print("   - Multiple models test failed")

if __name__ == "__main__":
    main()
