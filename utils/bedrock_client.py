"""
Bedrock Client Wrapper cho Load Testing với Inference Profile support
"""
import boto3
import json
import time
import logging
from typing import Dict, Any, Optional, List
from botocore.exceptions import ClientError, BotoCoreError
import asyncio
import aiohttp
import yaml
import os

logger = logging.getLogger(__name__)

class BedrockClient:
    """Wrapper class cho AWS Bedrock client với retry logic và error handling"""
    
    def __init__(self, region: str = "us-east-1", profile: Optional[str] = None):
        """
        Initialize Bedrock client
        
        Args:
            region: AWS region
            profile: AWS profile name
        """
        self.region = region
        self.profile = profile
        
        # Initialize boto3 session
        if profile:
            session = boto3.Session(profile_name=profile)
        else:
            session = boto3.Session()
            
        # Initialize clients
        self.bedrock_runtime = session.client('bedrock-runtime', region_name=region)
        self.bedrock_agent_runtime = session.client('bedrock-agent-runtime', region_name=region)
        self.bedrock = session.client('bedrock', region_name=region)
        
        # Retry configuration
        self.max_retries = 3
        self.backoff_factor = 2
        
        # Load model configurations
        self.model_configs = self._load_model_configs()
        
    def _load_model_configs(self) -> Dict[str, Any]:
        """Load model configurations from YAML file"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'models_config.yaml')
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Could not load model configs: {e}")
            return {}
    
    def _prepare_request_body(self, model_config: Dict[str, Any], prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Prepare request body based on model format
        
        Args:
            model_config: Model configuration
            prompt: Input prompt
            **kwargs: Additional parameters
            
        Returns:
            Formatted request body
        """
        request_format = model_config.get('request_format', 'anthropic')
        
        if request_format == 'anthropic':
            return {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": kwargs.get('max_tokens', model_config.get('max_tokens', 4096)),
                "temperature": kwargs.get('temperature', model_config.get('temperature', 0.7)),
                "top_p": kwargs.get('top_p', model_config.get('top_p', 0.9)),
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
        
        elif request_format == 'llama':
            return {
                "prompt": f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n",
                "max_gen_len": kwargs.get('max_tokens', model_config.get('max_tokens', 4096)),
                "temperature": kwargs.get('temperature', model_config.get('temperature', 0.7)),
                "top_p": kwargs.get('top_p', model_config.get('top_p', 0.9))
            }
        
        elif request_format == 'nova':
            return {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                "inferenceConfig": {
                    "max_new_tokens": kwargs.get('max_tokens', model_config.get('max_tokens', 4096)),
                    "temperature": kwargs.get('temperature', model_config.get('temperature', 0.7)),
                    "top_p": kwargs.get('top_p', model_config.get('top_p', 0.9))
                }
            }
        
        elif request_format == 'deepseek':
            return {
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": kwargs.get('max_tokens', model_config.get('max_tokens', 4096)),
                "temperature": kwargs.get('temperature', model_config.get('temperature', 0.7)),
                "top_p": kwargs.get('top_p', model_config.get('top_p', 0.9))
            }
        
        elif request_format == 'mistral':
            return {
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": kwargs.get('max_tokens', model_config.get('max_tokens', 4096)),
                "temperature": kwargs.get('temperature', model_config.get('temperature', 0.7)),
                "top_p": kwargs.get('top_p', model_config.get('top_p', 0.9))
            }
        
        else:
            # Default to anthropic format
            return {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": kwargs.get('max_tokens', model_config.get('max_tokens', 4096)),
                "temperature": kwargs.get('temperature', model_config.get('temperature', 0.7)),
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
    
    def _extract_response_text(self, response_body: Dict[str, Any], request_format: str) -> str:
        """
        Extract response text based on model format
        
        Args:
            response_body: Response from model
            request_format: Request format used
            
        Returns:
            Extracted text
        """
        try:
            if request_format == 'anthropic':
                return response_body.get('content', [{}])[0].get('text', '')
            
            elif request_format == 'llama':
                return response_body.get('generation', '')
            
            elif request_format == 'nova':
                if 'output' in response_body and 'message' in response_body['output']:
                    return response_body['output']['message']['content'][0]['text']
                return ''
            
            elif request_format in ['deepseek', 'mistral']:
                if 'choices' in response_body and len(response_body['choices']) > 0:
                    return response_body['choices'][0]['message']['content']
                return ''
            
            else:
                # Try common response formats
                if 'content' in response_body:
                    return response_body['content'][0].get('text', '')
                elif 'generation' in response_body:
                    return response_body['generation']
                elif 'completion' in response_body:
                    return response_body['completion']
                else:
                    return str(response_body)
                    
        except Exception as e:
            logger.warning(f"Could not extract response text: {e}")
            return str(response_body)
    
    def _get_token_usage(self, response_body: Dict[str, Any], request_format: str) -> Dict[str, int]:
        """
        Extract token usage from response
        
        Args:
            response_body: Response from model
            request_format: Request format used
            
        Returns:
            Token usage dictionary
        """
        try:
            if request_format == 'anthropic':
                usage = response_body.get('usage', {})
                return {
                    'input_tokens': usage.get('input_tokens', 0),
                    'output_tokens': usage.get('output_tokens', 0)
                }
            
            elif request_format == 'llama':
                return {
                    'input_tokens': response_body.get('prompt_token_count', 0),
                    'output_tokens': response_body.get('generation_token_count', 0)
                }
            
            elif request_format == 'nova':
                usage = response_body.get('usage', {})
                return {
                    'input_tokens': usage.get('inputTokens', 0),
                    'output_tokens': usage.get('outputTokens', 0)
                }
            
            elif request_format in ['deepseek', 'mistral']:
                usage = response_body.get('usage', {})
                return {
                    'input_tokens': usage.get('prompt_tokens', 0),
                    'output_tokens': usage.get('completion_tokens', 0)
                }
            
            else:
                return {'input_tokens': 0, 'output_tokens': 0}
                
        except Exception as e:
            logger.warning(f"Could not extract token usage: {e}")
            return {'input_tokens': 0, 'output_tokens': 0}
    
    def invoke_model(self, model_id: str, body: Dict[str, Any], 
                    accept: str = "application/json", 
                    content_type: str = "application/json") -> Dict[str, Any]:
        """
        Invoke foundation model với retry logic
        
        Args:
            model_id: Model identifier (có thể là inference profile ID)
            body: Request body
            accept: Accept header
            content_type: Content type header
            
        Returns:
            Response từ model
        """
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()
                
                response = self.bedrock_runtime.invoke_model(
                    modelId=model_id,
                    body=json.dumps(body),
                    accept=accept,
                    contentType=content_type
                )
                
                end_time = time.time()
                latency = end_time - start_time
                
                # Parse response
                response_body = json.loads(response['body'].read())
                
                return {
                    'response': response_body,
                    'latency': latency,
                    'status_code': response['ResponseMetadata']['HTTPStatusCode'],
                    'request_id': response['ResponseMetadata']['RequestId']
                }
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                
                if error_code == 'ThrottlingException' and attempt < self.max_retries - 1:
                    wait_time = self.backoff_factor ** attempt
                    logger.warning(f"Throttling detected, waiting {wait_time}s before retry")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"ClientError invoking model: {e}")
                    raise
                    
            except Exception as e:
                logger.error(f"Unexpected error invoking model: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.backoff_factor ** attempt)
                    continue
                else:
                    raise
                    
        raise Exception(f"Failed to invoke model after {self.max_retries} attempts")
    
    def invoke_model_by_name(self, model_name: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Invoke model by configuration name với automatic request formatting
        
        Args:
            model_name: Model name from configuration
            prompt: Input prompt
            **kwargs: Additional parameters
            
        Returns:
            Response từ model
        """
        # Get model configuration
        model_config = self.model_configs.get('foundation_models', {}).get(model_name)
        if not model_config:
            raise ValueError(f"Model configuration not found for: {model_name}")
        
        model_id = model_config['model_id']
        request_format = model_config.get('request_format', 'anthropic')
        
        # Prepare request body
        request_body = self._prepare_request_body(model_config, prompt, **kwargs)
        
        # Invoke model
        result = self.invoke_model(model_id, request_body)
        
        # Extract response text and token usage
        response_text = self._extract_response_text(result['response'], request_format)
        token_usage = self._get_token_usage(result['response'], request_format)
        
        # Calculate cost
        pricing = model_config.get('pricing', {})
        input_cost = (token_usage['input_tokens'] / 1000) * pricing.get('input_tokens', 0)
        output_cost = (token_usage['output_tokens'] / 1000) * pricing.get('output_tokens', 0)
        total_cost = input_cost + output_cost
        
        # Return enhanced result
        result.update({
            'response_text': response_text,
            'token_usage': token_usage,
            'cost': {
                'input_cost': input_cost,
                'output_cost': output_cost,
                'total_cost': total_cost
            },
            'model_name': model_name,
            'model_config': model_config
        })
        
        return result
    
    def invoke_model_with_response_stream(self, model_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke model với streaming response
        
        Args:
            model_id: Model identifier
            body: Request body
            
        Returns:
            Streaming response
        """
        try:
            start_time = time.time()
            
            response = self.bedrock_runtime.invoke_model_with_response_stream(
                modelId=model_id,
                body=json.dumps(body)
            )
            
            # Collect streaming response
            full_response = ""
            for event in response['body']:
                chunk = json.loads(event['chunk']['bytes'])
                if 'delta' in chunk:
                    full_response += chunk['delta'].get('text', '')
                elif 'completion' in chunk:
                    full_response += chunk['completion']
            
            end_time = time.time()
            latency = end_time - start_time
            
            return {
                'response': {'completion': full_response},
                'latency': latency,
                'streaming': True
            }
            
        except Exception as e:
            logger.error(f"Error in streaming invoke: {e}")
            raise
    
    def retrieve_and_generate(self, kb_id: str, query: str, 
                            retrieval_config: Optional[Dict] = None,
                            generation_config: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Query Knowledge Base
        
        Args:
            kb_id: Knowledge Base ID
            query: Query string
            retrieval_config: Retrieval configuration
            generation_config: Generation configuration
            
        Returns:
            Response từ Knowledge Base
        """
        try:
            start_time = time.time()
            
            # Use inference profile for Knowledge Base
            kb_config = self.model_configs.get('knowledge_base', {})
            model_arn = kb_config.get('model_arn', 
                f'arn:aws:bedrock:{self.region}::inference-profile/us.anthropic.claude-3-haiku-20240307-v1:0')
            
            request_body = {
                'input': {'text': query},
                'retrieveAndGenerateConfiguration': {
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': kb_id,
                        'modelArn': model_arn
                    }
                }
            }
            
            if retrieval_config:
                request_body['retrieveAndGenerateConfiguration']['knowledgeBaseConfiguration']['retrievalConfiguration'] = retrieval_config
                
            if generation_config:
                request_body['retrieveAndGenerateConfiguration']['knowledgeBaseConfiguration']['generationConfiguration'] = generation_config
            
            response = self.bedrock_agent_runtime.retrieve_and_generate(**request_body)
            
            end_time = time.time()
            latency = end_time - start_time
            
            return {
                'response': response,
                'latency': latency,
                'citations': response.get('citations', []),
                'session_id': response.get('sessionId')
            }
            
        except Exception as e:
            logger.error(f"Error querying Knowledge Base: {e}")
            raise
    
    def invoke_agent(self, agent_id: str, agent_alias_id: str, session_id: str, 
                    input_text: str) -> Dict[str, Any]:
        """
        Invoke Bedrock Agent
        
        Args:
            agent_id: Agent ID
            agent_alias_id: Agent alias ID
            session_id: Session ID
            input_text: Input text
            
        Returns:
            Response từ Agent
        """
        try:
            start_time = time.time()
            
            response = self.bedrock_agent_runtime.invoke_agent(
                agentId=agent_id,
                agentAliasId=agent_alias_id,
                sessionId=session_id,
                inputText=input_text
            )
            
            # Collect streaming response
            full_response = ""
            for event in response['completion']:
                if 'chunk' in event:
                    chunk_data = event['chunk']
                    if 'bytes' in chunk_data:
                        chunk_text = chunk_data['bytes'].decode('utf-8')
                        full_response += chunk_text
            
            end_time = time.time()
            latency = end_time - start_time
            
            return {
                'response': full_response,
                'latency': latency,
                'session_id': session_id
            }
            
        except Exception as e:
            logger.error(f"Error invoking agent: {e}")
            raise
    
    def apply_guardrail(self, guardrail_id: str, guardrail_version: str, 
                       source: str, content: List[Dict]) -> Dict[str, Any]:
        """
        Apply Guardrail to content
        
        Args:
            guardrail_id: Guardrail ID
            guardrail_version: Guardrail version
            source: Source type (INPUT or OUTPUT)
            content: Content to check
            
        Returns:
            Guardrail response
        """
        try:
            start_time = time.time()
            
            response = self.bedrock_runtime.apply_guardrail(
                guardrailIdentifier=guardrail_id,
                guardrailVersion=guardrail_version,
                source=source,
                content=content
            )
            
            end_time = time.time()
            latency = end_time - start_time
            
            return {
                'response': response,
                'latency': latency,
                'action': response.get('action'),
                'assessments': response.get('assessments', [])
            }
            
        except Exception as e:
            logger.error(f"Error applying guardrail: {e}")
            raise
    
    def create_model_invocation_job(self, job_name: str, role_arn: str, 
                                  model_id: str, input_data_config: Dict,
                                  output_data_config: Dict) -> Dict[str, Any]:
        """
        Create batch inference job
        
        Args:
            job_name: Job name
            role_arn: IAM role ARN
            model_id: Model ID (có thể là inference profile)
            input_data_config: Input data configuration
            output_data_config: Output data configuration
            
        Returns:
            Job creation response
        """
        try:
            response = self.bedrock.create_model_invocation_job(
                jobName=job_name,
                roleArn=role_arn,
                modelId=model_id,
                inputDataConfig=input_data_config,
                outputDataConfig=output_data_config
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error creating batch job: {e}")
            raise
    
    def get_model_invocation_job(self, job_identifier: str) -> Dict[str, Any]:
        """
        Get batch inference job status
        
        Args:
            job_identifier: Job identifier
            
        Returns:
            Job status response
        """
        try:
            response = self.bedrock.get_model_invocation_job(
                jobIdentifier=job_identifier
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting batch job status: {e}")
            raise
    
    def list_available_models(self) -> List[str]:
        """
        List available model names from configuration
        
        Returns:
            List of model names
        """
        return list(self.model_configs.get('foundation_models', {}).keys())
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        Get model information
        
        Args:
            model_name: Model name
            
        Returns:
            Model information
        """
        return self.model_configs.get('foundation_models', {}).get(model_name, {})

class AsyncBedrockClient:
    """Async version của BedrockClient cho concurrent testing"""
    
    def __init__(self, region: str = "us-east-1", profile: Optional[str] = None):
        self.sync_client = BedrockClient(region, profile)
        
    async def invoke_model_async(self, model_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Async wrapper cho model invocation
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self.sync_client.invoke_model, 
            model_id, 
            body
        )
    
    async def invoke_model_by_name_async(self, model_name: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Async wrapper cho model invocation by name
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.sync_client.invoke_model_by_name,
            model_name,
            prompt,
            **kwargs
        )
    
    async def retrieve_and_generate_async(self, kb_id: str, query: str) -> Dict[str, Any]:
        """
        Async wrapper cho Knowledge Base query
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.sync_client.retrieve_and_generate,
            kb_id,
            query
        )
