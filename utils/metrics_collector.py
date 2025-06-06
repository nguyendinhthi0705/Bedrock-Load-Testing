"""
Metrics Collector cho Bedrock Load Testing
"""
import time
import threading
import psutil
import boto3
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics

logger = logging.getLogger(__name__)

class MetricsCollector:
    """Thu thập và lưu trữ metrics trong quá trình load testing"""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        
        # Metrics storage
        self.metrics = defaultdict(list)
        self.request_metrics = []
        self.error_metrics = []
        self.cost_metrics = defaultdict(float)
        
        # System metrics
        self.system_metrics = defaultdict(deque)
        self.system_monitoring_active = False
        self.system_monitor_thread = None
        
        # Timing
        self.start_time = None
        self.end_time = None
        
        # Thread safety
        self.lock = threading.Lock()
        
    def start_monitoring(self):
        """Bắt đầu thu thập metrics"""
        self.start_time = time.time()
        self.system_monitoring_active = True
        
        # Start system monitoring thread
        self.system_monitor_thread = threading.Thread(target=self._monitor_system_resources)
        self.system_monitor_thread.daemon = True
        self.system_monitor_thread.start()
        
        logger.info("Metrics monitoring started")
    
    def stop_monitoring(self):
        """Dừng thu thập metrics"""
        self.end_time = time.time()
        self.system_monitoring_active = False
        
        if self.system_monitor_thread:
            self.system_monitor_thread.join(timeout=5)
            
        logger.info("Metrics monitoring stopped")
    
    def record_request(self, request_type: str, latency: float, success: bool, 
                      tokens_input: int = 0, tokens_output: int = 0, 
                      cost: float = 0.0, error: Optional[str] = None):
        """
        Ghi lại metrics cho một request
        
        Args:
            request_type: Loại request (foundation_model, knowledge_base, agent, etc.)
            latency: Thời gian phản hồi (giây)
            success: Request thành công hay không
            tokens_input: Số input tokens
            tokens_output: Số output tokens
            cost: Chi phí ước tính
            error: Thông tin lỗi nếu có
        """
        with self.lock:
            timestamp = time.time()
            
            request_data = {
                'timestamp': timestamp,
                'request_type': request_type,
                'latency': latency,
                'success': success,
                'tokens_input': tokens_input,
                'tokens_output': tokens_output,
                'cost': cost,
                'error': error
            }
            
            self.request_metrics.append(request_data)
            
            # Update aggregated metrics
            self.metrics[f'{request_type}_latency'].append(latency)
            self.metrics[f'{request_type}_success'].append(1 if success else 0)
            self.metrics[f'{request_type}_tokens_input'].append(tokens_input)
            self.metrics[f'{request_type}_tokens_output'].append(tokens_output)
            
            # Update cost metrics
            self.cost_metrics[request_type] += cost
            self.cost_metrics['total'] += cost
            
            # Record errors
            if not success and error:
                self.error_metrics.append({
                    'timestamp': timestamp,
                    'request_type': request_type,
                    'error': error
                })
    
    def _monitor_system_resources(self):
        """Monitor system resources trong background thread"""
        while self.system_monitoring_active:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                
                # Memory usage
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                memory_used_gb = memory.used / (1024**3)
                
                # Network I/O
                network = psutil.net_io_counters()
                
                # Disk I/O
                disk = psutil.disk_io_counters()
                
                timestamp = time.time()
                
                with self.lock:
                    self.system_metrics['cpu_percent'].append((timestamp, cpu_percent))
                    self.system_metrics['memory_percent'].append((timestamp, memory_percent))
                    self.system_metrics['memory_used_gb'].append((timestamp, memory_used_gb))
                    self.system_metrics['network_bytes_sent'].append((timestamp, network.bytes_sent))
                    self.system_metrics['network_bytes_recv'].append((timestamp, network.bytes_recv))
                    
                    if disk:
                        self.system_metrics['disk_read_bytes'].append((timestamp, disk.read_bytes))
                        self.system_metrics['disk_write_bytes'].append((timestamp, disk.write_bytes))
                    
                    # Keep only last 1000 data points
                    for key in self.system_metrics:
                        if len(self.system_metrics[key]) > 1000:
                            self.system_metrics[key].popleft()
                
                time.sleep(5)  # Collect every 5 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring system resources: {e}")
                time.sleep(5)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Tạo tổng kết performance metrics"""
        with self.lock:
            summary = {}
            
            # Overall metrics
            total_requests = len(self.request_metrics)
            successful_requests = sum(1 for r in self.request_metrics if r['success'])
            failed_requests = total_requests - successful_requests
            
            summary['overall'] = {
                'total_requests': total_requests,
                'successful_requests': successful_requests,
                'failed_requests': failed_requests,
                'success_rate': successful_requests / total_requests if total_requests > 0 else 0,
                'test_duration': self.end_time - self.start_time if self.end_time else time.time() - self.start_time,
                'requests_per_second': total_requests / (self.end_time - self.start_time) if self.end_time and self.start_time else 0
            }
            
            # Latency metrics by request type
            request_types = set(r['request_type'] for r in self.request_metrics)
            
            for req_type in request_types:
                type_requests = [r for r in self.request_metrics if r['request_type'] == req_type]
                latencies = [r['latency'] for r in type_requests if r['success']]
                
                if latencies:
                    summary[req_type] = {
                        'total_requests': len(type_requests),
                        'successful_requests': len(latencies),
                        'success_rate': len(latencies) / len(type_requests),
                        'avg_latency': statistics.mean(latencies),
                        'median_latency': statistics.median(latencies),
                        'p95_latency': self._percentile(latencies, 95),
                        'p99_latency': self._percentile(latencies, 99),
                        'min_latency': min(latencies),
                        'max_latency': max(latencies)
                    }
            
            return summary
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Tạo tổng kết cost metrics"""
        with self.lock:
            cost_summary = dict(self.cost_metrics)
            
            # Add token usage summary
            token_summary = {}
            for req_type in set(r['request_type'] for r in self.request_metrics):
                type_requests = [r for r in self.request_metrics if r['request_type'] == req_type]
                
                total_input_tokens = sum(r['tokens_input'] for r in type_requests)
                total_output_tokens = sum(r['tokens_output'] for r in type_requests)
                
                token_summary[req_type] = {
                    'total_input_tokens': total_input_tokens,
                    'total_output_tokens': total_output_tokens,
                    'total_tokens': total_input_tokens + total_output_tokens
                }
            
            return {
                'costs': cost_summary,
                'tokens': token_summary
            }
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Tạo tổng kết error metrics"""
        with self.lock:
            error_counts = defaultdict(int)
            error_by_type = defaultdict(list)
            
            for error in self.error_metrics:
                error_counts[error['error']] += 1
                error_by_type[error['request_type']].append(error['error'])
            
            return {
                'total_errors': len(self.error_metrics),
                'error_counts': dict(error_counts),
                'errors_by_type': dict(error_by_type)
            }
    
    def get_system_metrics_summary(self) -> Dict[str, Any]:
        """Tạo tổng kết system metrics"""
        with self.lock:
            summary = {}
            
            for metric_name, data_points in self.system_metrics.items():
                if data_points:
                    values = [point[1] for point in data_points]
                    summary[metric_name] = {
                        'avg': statistics.mean(values),
                        'max': max(values),
                        'min': min(values),
                        'current': values[-1] if values else 0
                    }
            
            return summary
    
    def export_raw_data(self) -> Dict[str, Any]:
        """Export tất cả raw data"""
        with self.lock:
            return {
                'request_metrics': self.request_metrics,
                'error_metrics': self.error_metrics,
                'system_metrics': {k: list(v) for k, v in self.system_metrics.items()},
                'cost_metrics': dict(self.cost_metrics),
                'test_info': {
                    'start_time': self.start_time,
                    'end_time': self.end_time,
                    'duration': self.end_time - self.start_time if self.end_time else None
                }
            }
    
    def send_to_cloudwatch(self, namespace: str = "BedrockLoadTest"):
        """Gửi metrics lên CloudWatch"""
        try:
            summary = self.get_performance_summary()
            
            # Prepare metrics data
            metric_data = []
            
            # Overall metrics
            if 'overall' in summary:
                overall = summary['overall']
                metric_data.extend([
                    {
                        'MetricName': 'TotalRequests',
                        'Value': overall['total_requests'],
                        'Unit': 'Count'
                    },
                    {
                        'MetricName': 'SuccessRate',
                        'Value': overall['success_rate'] * 100,
                        'Unit': 'Percent'
                    },
                    {
                        'MetricName': 'RequestsPerSecond',
                        'Value': overall['requests_per_second'],
                        'Unit': 'Count/Second'
                    }
                ])
            
            # Send metrics in batches (CloudWatch limit is 20 per call)
            for i in range(0, len(metric_data), 20):
                batch = metric_data[i:i+20]
                self.cloudwatch.put_metric_data(
                    Namespace=namespace,
                    MetricData=batch
                )
            
            logger.info(f"Sent {len(metric_data)} metrics to CloudWatch")
            
        except Exception as e:
            logger.error(f"Error sending metrics to CloudWatch: {e}")
    
    @staticmethod
    def _percentile(data: List[float], percentile: float) -> float:
        """Tính percentile"""
        if not data:
            return 0
        
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
