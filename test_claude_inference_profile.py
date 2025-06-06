#!/usr/bin/env python3
"""
Test script để gọi Claude 3.5 Sonnet v2 với inference profile
"""

import boto3
import json
import time
from botocore.exceptions import ClientError

def test_claude_with_inference_profile():
    """Test gọi Claude 3.5 Sonnet v2 với inference profile"""
    
    # Khởi tạo Bedrock client với profile default
    bedrock_runtime = boto3.client(
        'bedrock-runtime',
        region_name='us-east-1',
        # Có thể thêm profile_name='default' nếu cần
    )
    
    # Sử dụng inference profile ID thay vì model ID trực tiếp
    inference_profile_id = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
    
    # Tạo request body
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "messages": [
            {
                "role": "user",
                "content": "Hello! Can you tell me what model you are and confirm that you're working correctly?"
            }
        ]
    }
    
    try:
        print(f"Testing với inference profile: {inference_profile_id}")
        print("Đang gửi request...")
        
        start_time = time.time()
        
        # Gọi InvokeModel với inference profile
        response = bedrock_runtime.invoke_model(
            modelId=inference_profile_id,  # Sử dụng inference profile ID
            body=json.dumps(request_body),
            contentType='application/json',
            accept='application/json'
        )
        
        end_time = time.time()
        latency = end_time - start_time
        
        # Parse response
        response_body = json.loads(response['body'].read())
        
        print(f"✅ SUCCESS!")
        print(f"⏱️  Latency: {latency:.2f} seconds")
        print(f"📝 Response:")
        print(f"   Content: {response_body['content'][0]['text']}")
        print(f"   Input tokens: {response_body['usage']['input_tokens']}")
        print(f"   Output tokens: {response_body['usage']['output_tokens']}")
        
        return True
        
    except ClientError as e:
        print(f"❌ AWS Client Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

def test_other_models():
    """Test một số model khác để so sánh"""
    
    bedrock_runtime = boto3.client(
        'bedrock-runtime',
        region_name='us-east-1'
    )
    
    # Test các inference profile khác
    test_models = [
        {
            "name": "Claude 3.5 Haiku",
            "id": "us.anthropic.claude-3-5-haiku-20241022-v1:0"
        },
        {
            "name": "Nova Lite",
            "id": "us.amazon.nova-lite-v1:0"
        }
    ]
    
    for model in test_models:
        print(f"\n--- Testing {model['name']} ---")
        
        # Request body cho Nova models sẽ khác
        if "nova" in model['id']:
            request_body = {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "text": f"Hello! I'm testing {model['name']}. Please respond briefly."
                            }
                        ]
                    }
                ],
                "inferenceConfig": {
                    "max_new_tokens": 100
                }
            }
        else:
            # Claude models
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 100,
                "messages": [
                    {
                        "role": "user",
                        "content": f"Hello! I'm testing {model['name']}. Please respond briefly."
                    }
                ]
            }
        
        try:
            start_time = time.time()
            
            response = bedrock_runtime.invoke_model(
                modelId=model['id'],
                body=json.dumps(request_body),
                contentType='application/json',
                accept='application/json'
            )
            
            end_time = time.time()
            latency = end_time - start_time
            
            response_body = json.loads(response['body'].read())
            
            print(f"✅ {model['name']} - SUCCESS! (Latency: {latency:.2f}s)")
            
            # Parse response based on model type
            if "nova" in model['id']:
                if 'output' in response_body and 'message' in response_body['output']:
                    content = response_body['output']['message']['content'][0]['text']
                    print(f"   Content: {content[:100]}...")
            else:
                if 'content' in response_body:
                    content = response_body['content'][0]['text']
                    print(f"   Content: {content[:100]}...")
            
        except Exception as e:
            print(f"❌ {model['name']} - FAILED: {e}")

if __name__ == "__main__":
    print("🧪 Testing AWS Bedrock với Inference Profiles")
    print("=" * 50)
    
    # Test Claude 3.5 Sonnet v2
    print("\n1. Testing Claude 3.5 Sonnet v2 với inference profile:")
    success = test_claude_with_inference_profile()
    
    if success:
        print("\n2. Testing một số model khác:")
        test_other_models()
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")
