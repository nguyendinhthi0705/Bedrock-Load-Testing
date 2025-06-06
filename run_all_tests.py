#!/usr/bin/env python3
"""
Master script để chạy tất cả load tests cho Bedrock
"""

import os
import sys
import time
import logging
import argparse
import subprocess
import json
from datetime import datetime
from typing import List, Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BedrockTestSuite:
    """Test suite chính cho tất cả Bedrock load tests"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.results = {}
        self.start_time = None
        self.end_time = None
        
    def run_foundation_model_test(self, models: List[str] = None) -> Dict[str, Any]:
        """Chạy Foundation Model load test"""
        logger.info("Starting Foundation Model load test...")
        
        cmd = ["python", "scripts/foundation_model_test.py"]
        
        if models:
            cmd.extend(["--models"] + models)
            
        cmd.extend([
            "--config", f"{self.config_dir}/test_config.yaml",
            "--models-config", f"{self.config_dir}/models_config.yaml"
        ])
        
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=3600  # 1 hour timeout
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            logger.error("Foundation Model test timed out")
            return {
                "success": False,
                "error": "Test timed out after 1 hour"
            }
        except Exception as e:
            logger.error(f"Error running Foundation Model test: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def run_knowledge_base_test(self, kb_id: str = None) -> Dict[str, Any]:
        """Chạy Knowledge Base load test"""
        logger.info("Starting Knowledge Base load test...")
        
        cmd = ["python", "scripts/knowledge_base_test.py"]
        
        if kb_id:
            cmd.extend(["--kb-id", kb_id])
            
        cmd.extend([
            "--config", f"{self.config_dir}/test_config.yaml",
            "--models-config", f"{self.config_dir}/models_config.yaml"
        ])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=2400  # 40 minutes timeout
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            logger.error("Knowledge Base test timed out")
            return {
                "success": False,
                "error": "Test timed out after 40 minutes"
            }
        except Exception as e:
            logger.error(f"Error running Knowledge Base test: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def run_agent_test(self, agent_id: str = None) -> Dict[str, Any]:
        """Chạy Agent load test"""
        logger.info("Starting Agent load test...")
        
        cmd = ["python", "scripts/agent_test.py"]
        
        if agent_id:
            cmd.extend(["--agent-id", agent_id])
            
        cmd.extend([
            "--config", f"{self.config_dir}/test_config.yaml",
            "--models-config", f"{self.config_dir}/models_config.yaml"
        ])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=2400  # 40 minutes timeout
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            logger.error("Agent test timed out")
            return {
                "success": False,
                "error": "Test timed out after 40 minutes"
            }
        except Exception as e:
            logger.error(f"Error running Agent test: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def run_batch_inference_test(self) -> Dict[str, Any]:
        """Chạy Batch Inference test"""
        logger.info("Starting Batch Inference test...")
        
        cmd = [
            "python", "scripts/batch_inference_test.py",
            "--config", f"{self.config_dir}/test_config.yaml",
            "--models-config", f"{self.config_dir}/models_config.yaml"
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=7200  # 2 hours timeout for batch jobs
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            logger.error("Batch Inference test timed out")
            return {
                "success": False,
                "error": "Test timed out after 2 hours"
            }
        except Exception as e:
            logger.error(f"Error running Batch Inference test: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def run_guardrails_test(self, guardrail_id: str = None) -> Dict[str, Any]:
        """Chạy Guardrails test"""
        logger.info("Starting Guardrails test...")
        
        cmd = ["python", "scripts/guardrails_test.py"]
        
        if guardrail_id:
            cmd.extend(["--guardrail-id", guardrail_id])
            
        cmd.extend([
            "--config", f"{self.config_dir}/test_config.yaml",
            "--models-config", f"{self.config_dir}/models_config.yaml"
        ])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes timeout
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            logger.error("Guardrails test timed out")
            return {
                "success": False,
                "error": "Test timed out after 30 minutes"
            }
        except Exception as e:
            logger.error(f"Error running Guardrails test: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def run_all_tests(self, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """Chạy tất cả tests theo cấu hình"""
        logger.info("Starting comprehensive Bedrock load test suite...")
        
        self.start_time = time.time()
        
        # Foundation Model tests
        if test_config.get('run_foundation_models', True):
            logger.info("="*50)
            logger.info("FOUNDATION MODEL TESTS")
            logger.info("="*50)
            
            models = test_config.get('foundation_models', None)
            self.results['foundation_models'] = self.run_foundation_model_test(models)
            
            if self.results['foundation_models']['success']:
                logger.info("✅ Foundation Model tests completed successfully")
            else:
                logger.error("❌ Foundation Model tests failed")
            
            # Wait between test suites
            time.sleep(30)
        
        # Knowledge Base tests
        if test_config.get('run_knowledge_base', False):
            logger.info("="*50)
            logger.info("KNOWLEDGE BASE TESTS")
            logger.info("="*50)
            
            kb_id = test_config.get('knowledge_base_id')
            if kb_id:
                self.results['knowledge_base'] = self.run_knowledge_base_test(kb_id)
                
                if self.results['knowledge_base']['success']:
                    logger.info("✅ Knowledge Base tests completed successfully")
                else:
                    logger.error("❌ Knowledge Base tests failed")
            else:
                logger.warning("⚠️ Knowledge Base ID not provided, skipping KB tests")
                self.results['knowledge_base'] = {
                    "success": False,
                    "error": "Knowledge Base ID not provided"
                }
            
            time.sleep(30)
        
        # Agent tests
        if test_config.get('run_agent', False):
            logger.info("="*50)
            logger.info("AGENT TESTS")
            logger.info("="*50)
            
            agent_id = test_config.get('agent_id')
            if agent_id:
                self.results['agent'] = self.run_agent_test(agent_id)
                
                if self.results['agent']['success']:
                    logger.info("✅ Agent tests completed successfully")
                else:
                    logger.error("❌ Agent tests failed")
            else:
                logger.warning("⚠️ Agent ID not provided, skipping Agent tests")
                self.results['agent'] = {
                    "success": False,
                    "error": "Agent ID not provided"
                }
            
            time.sleep(30)
        
        # Batch Inference tests
        if test_config.get('run_batch_inference', False):
            logger.info("="*50)
            logger.info("BATCH INFERENCE TESTS")
            logger.info("="*50)
            
            self.results['batch_inference'] = self.run_batch_inference_test()
            
            if self.results['batch_inference']['success']:
                logger.info("✅ Batch Inference tests completed successfully")
            else:
                logger.error("❌ Batch Inference tests failed")
            
            time.sleep(30)
        
        # Guardrails tests
        if test_config.get('run_guardrails', False):
            logger.info("="*50)
            logger.info("GUARDRAILS TESTS")
            logger.info("="*50)
            
            guardrail_id = test_config.get('guardrail_id')
            if guardrail_id:
                self.results['guardrails'] = self.run_guardrails_test(guardrail_id)
                
                if self.results['guardrails']['success']:
                    logger.info("✅ Guardrails tests completed successfully")
                else:
                    logger.error("❌ Guardrails tests failed")
            else:
                logger.warning("⚠️ Guardrail ID not provided, skipping Guardrails tests")
                self.results['guardrails'] = {
                    "success": False,
                    "error": "Guardrail ID not provided"
                }
        
        self.end_time = time.time()
        
        # Generate final report
        return self._generate_final_report()
    
    def _generate_final_report(self) -> Dict[str, Any]:
        """Tạo báo cáo tổng kết"""
        logger.info("Generating final test suite report...")
        
        total_duration = self.end_time - self.start_time if self.end_time and self.start_time else 0
        
        # Count successes and failures
        successful_tests = sum(1 for result in self.results.values() if result.get('success'))
        total_tests = len(self.results)
        
        final_report = {
            'test_suite_info': {
                'timestamp': datetime.now().isoformat(),
                'total_duration': total_duration,
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'failed_tests': total_tests - successful_tests,
                'success_rate': successful_tests / total_tests if total_tests > 0 else 0
            },
            'test_results': self.results
        }
        
        # Save final report
        os.makedirs('reports', exist_ok=True)
        report_file = f"reports/bedrock_test_suite_{int(time.time())}.json"
        
        with open(report_file, 'w') as f:
            json.dump(final_report, f, indent=2)
        
        logger.info(f"Final report saved to: {report_file}")
        
        # Print summary
        self._print_final_summary(final_report)
        
        return final_report
    
    def _print_final_summary(self, report: Dict[str, Any]):
        """In tóm tắt cuối cùng"""
        info = report['test_suite_info']
        
        print("\n" + "="*80)
        print("BEDROCK LOAD TEST SUITE SUMMARY")
        print("="*80)
        
        print(f"Total Duration: {info['total_duration']:.2f} seconds ({info['total_duration']/60:.1f} minutes)")
        print(f"Total Tests: {info['total_tests']}")
        print(f"Successful Tests: {info['successful_tests']}")
        print(f"Failed Tests: {info['failed_tests']}")
        print(f"Success Rate: {info['success_rate']:.2%}")
        
        print(f"\nTest Results:")
        for test_name, result in report['test_results'].items():
            status = "✅ PASSED" if result.get('success') else "❌ FAILED"
            print(f"  {test_name}: {status}")
            
            if not result.get('success') and result.get('error'):
                print(f"    Error: {result['error']}")
        
        print("\n" + "="*80)

def main():
    parser = argparse.ArgumentParser(description='Run comprehensive Bedrock load test suite')
    parser.add_argument('--config-dir', default='config', help='Configuration directory')
    parser.add_argument('--foundation-models', nargs='+', help='Foundation models to test')
    parser.add_argument('--kb-id', help='Knowledge Base ID')
    parser.add_argument('--agent-id', help='Agent ID')
    parser.add_argument('--guardrail-id', help='Guardrail ID')
    parser.add_argument('--skip-foundation', action='store_true', help='Skip foundation model tests')
    parser.add_argument('--enable-kb', action='store_true', help='Enable Knowledge Base tests')
    parser.add_argument('--enable-agent', action='store_true', help='Enable Agent tests')
    parser.add_argument('--enable-batch', action='store_true', help='Enable Batch Inference tests')
    parser.add_argument('--enable-guardrails', action='store_true', help='Enable Guardrails tests')
    
    args = parser.parse_args()
    
    # Build test configuration
    test_config = {
        'run_foundation_models': not args.skip_foundation,
        'foundation_models': args.foundation_models,
        'run_knowledge_base': args.enable_kb,
        'knowledge_base_id': args.kb_id,
        'run_agent': args.enable_agent,
        'agent_id': args.agent_id,
        'run_batch_inference': args.enable_batch,
        'run_guardrails': args.enable_guardrails,
        'guardrail_id': args.guardrail_id
    }
    
    # Initialize and run test suite
    suite = BedrockTestSuite(args.config_dir)
    final_report = suite.run_all_tests(test_config)
    
    # Exit with appropriate code
    if final_report['test_suite_info']['failed_tests'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
