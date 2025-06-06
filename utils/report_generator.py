"""
Report Generator cho Bedrock Load Testing
Tạo báo cáo HTML và visualizations
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from jinja2 import Template

class ReportGenerator:
    """Tạo báo cáo chi tiết cho load testing results"""
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Set up plotting style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    def generate_comprehensive_report(self, test_data: Dict[str, Any], 
                                    report_name: str = None) -> str:
        """
        Tạo báo cáo toàn diện với charts và analysis
        
        Args:
            test_data: Dữ liệu test results
            report_name: Tên file báo cáo
            
        Returns:
            Path to generated report
        """
        if not report_name:
            report_name = f"bedrock_load_test_report_{int(time.time())}"
        
        # Create charts
        charts = self._generate_charts(test_data, report_name)
        
        # Generate HTML report
        html_report = self._generate_html_report(test_data, charts, report_name)
        
        # Generate CSV data
        csv_files = self._generate_csv_reports(test_data, report_name)
        
        return html_report
    
    def _generate_charts(self, test_data: Dict[str, Any], report_name: str) -> Dict[str, str]:
        """Tạo các charts cho báo cáo"""
        charts = {}
        
        # Performance metrics chart
        if 'performance' in test_data:
            charts['performance'] = self._create_performance_chart(
                test_data['performance'], report_name
            )
        
        # Cost analysis chart
        if 'costs' in test_data:
            charts['costs'] = self._create_cost_chart(
                test_data['costs'], report_name
            )
        
        # Latency distribution chart
        if 'raw_data' in test_data and 'request_metrics' in test_data['raw_data']:
            charts['latency_dist'] = self._create_latency_distribution_chart(
                test_data['raw_data']['request_metrics'], report_name
            )
        
        # Throughput over time chart
        if 'raw_data' in test_data and 'request_metrics' in test_data['raw_data']:
            charts['throughput'] = self._create_throughput_chart(
                test_data['raw_data']['request_metrics'], report_name
            )
        
        # Error analysis chart
        if 'errors' in test_data and test_data['errors']['total_errors'] > 0:
            charts['errors'] = self._create_error_chart(
                test_data['errors'], report_name
            )
        
        # System metrics chart
        if 'system_metrics' in test_data:
            charts['system'] = self._create_system_metrics_chart(
                test_data['system_metrics'], report_name
            )
        
        return charts
    
    def _create_performance_chart(self, performance_data: Dict, report_name: str) -> str:
        """Tạo performance metrics chart"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Performance Metrics Overview', fontsize=16, fontweight='bold')
        
        # Extract data for different request types
        request_types = []
        success_rates = []
        avg_latencies = []
        p95_latencies = []
        total_requests = []
        
        for key, metrics in performance_data.items():
            if key != 'overall' and isinstance(metrics, dict):
                request_types.append(key.replace('_', ' ').title())
                success_rates.append(metrics.get('success_rate', 0) * 100)
                avg_latencies.append(metrics.get('avg_latency', 0))
                p95_latencies.append(metrics.get('p95_latency', 0))
                total_requests.append(metrics.get('total_requests', 0))
        
        if request_types:
            # Success Rate
            axes[0, 0].bar(request_types, success_rates, color='green', alpha=0.7)
            axes[0, 0].set_title('Success Rate by Request Type')
            axes[0, 0].set_ylabel('Success Rate (%)')
            axes[0, 0].tick_params(axis='x', rotation=45)
            
            # Average Latency
            axes[0, 1].bar(request_types, avg_latencies, color='blue', alpha=0.7)
            axes[0, 1].set_title('Average Latency by Request Type')
            axes[0, 1].set_ylabel('Latency (seconds)')
            axes[0, 1].tick_params(axis='x', rotation=45)
            
            # P95 Latency
            axes[1, 0].bar(request_types, p95_latencies, color='orange', alpha=0.7)
            axes[1, 0].set_title('P95 Latency by Request Type')
            axes[1, 0].set_ylabel('Latency (seconds)')
            axes[1, 0].tick_params(axis='x', rotation=45)
            
            # Total Requests
            axes[1, 1].bar(request_types, total_requests, color='purple', alpha=0.7)
            axes[1, 1].set_title('Total Requests by Type')
            axes[1, 1].set_ylabel('Number of Requests')
            axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        chart_path = os.path.join(self.output_dir, f"{report_name}_performance.png")
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return chart_path
    
    def _create_cost_chart(self, cost_data: Dict, report_name: str) -> str:
        """Tạo cost analysis chart"""
        fig, axes = plt.subplots(1, 2, figsize=(15, 6))
        fig.suptitle('Cost Analysis', fontsize=16, fontweight='bold')
        
        costs = cost_data.get('costs', {})
        tokens = cost_data.get('tokens', {})
        
        # Cost breakdown pie chart
        if costs:
            cost_items = [(k, v) for k, v in costs.items() if k != 'total' and v > 0]
            if cost_items:
                labels, values = zip(*cost_items)
                axes[0].pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
                axes[0].set_title('Cost Breakdown by Service')
        
        # Token usage chart
        if tokens:
            token_types = []
            input_tokens = []
            output_tokens = []
            
            for service, token_data in tokens.items():
                if isinstance(token_data, dict):
                    token_types.append(service.replace('_', ' ').title())
                    input_tokens.append(token_data.get('total_input_tokens', 0))
                    output_tokens.append(token_data.get('total_output_tokens', 0))
            
            if token_types:
                x = np.arange(len(token_types))
                width = 0.35
                
                axes[1].bar(x - width/2, input_tokens, width, label='Input Tokens', alpha=0.7)
                axes[1].bar(x + width/2, output_tokens, width, label='Output Tokens', alpha=0.7)
                
                axes[1].set_title('Token Usage by Service')
                axes[1].set_ylabel('Number of Tokens')
                axes[1].set_xticks(x)
                axes[1].set_xticklabels(token_types, rotation=45)
                axes[1].legend()
        
        plt.tight_layout()
        
        chart_path = os.path.join(self.output_dir, f"{report_name}_costs.png")
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return chart_path
    
    def _create_latency_distribution_chart(self, request_metrics: List[Dict], 
                                         report_name: str) -> str:
        """Tạo latency distribution chart"""
        fig, axes = plt.subplots(1, 2, figsize=(15, 6))
        fig.suptitle('Latency Distribution Analysis', fontsize=16, fontweight='bold')
        
        # Extract successful requests
        successful_requests = [r for r in request_metrics if r.get('success')]
        
        if successful_requests:
            latencies = [r['latency'] for r in successful_requests]
            
            # Histogram
            axes[0].hist(latencies, bins=50, alpha=0.7, color='skyblue', edgecolor='black')
            axes[0].set_title('Latency Distribution')
            axes[0].set_xlabel('Latency (seconds)')
            axes[0].set_ylabel('Frequency')
            axes[0].axvline(np.mean(latencies), color='red', linestyle='--', 
                           label=f'Mean: {np.mean(latencies):.3f}s')
            axes[0].axvline(np.percentile(latencies, 95), color='orange', linestyle='--',
                           label=f'P95: {np.percentile(latencies, 95):.3f}s')
            axes[0].legend()
            
            # Box plot by request type
            request_types = list(set(r['request_type'] for r in successful_requests))
            latency_by_type = []
            labels = []
            
            for req_type in request_types:
                type_latencies = [r['latency'] for r in successful_requests 
                                if r['request_type'] == req_type]
                if type_latencies:
                    latency_by_type.append(type_latencies)
                    labels.append(req_type.replace('_', ' ').title())
            
            if latency_by_type:
                axes[1].boxplot(latency_by_type, labels=labels)
                axes[1].set_title('Latency by Request Type')
                axes[1].set_ylabel('Latency (seconds)')
                axes[1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        chart_path = os.path.join(self.output_dir, f"{report_name}_latency_dist.png")
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return chart_path
    
    def _create_throughput_chart(self, request_metrics: List[Dict], 
                               report_name: str) -> str:
        """Tạo throughput over time chart"""
        fig, ax = plt.subplots(1, 1, figsize=(15, 6))
        fig.suptitle('Throughput Over Time', fontsize=16, fontweight='bold')
        
        if request_metrics:
            # Convert to DataFrame for easier manipulation
            df = pd.DataFrame(request_metrics)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            
            # Calculate throughput in 30-second windows
            df.set_index('timestamp', inplace=True)
            throughput = df.resample('30S').size()
            
            # Plot throughput
            ax.plot(throughput.index, throughput.values, marker='o', linewidth=2)
            ax.set_title('Requests per 30-second Window')
            ax.set_xlabel('Time')
            ax.set_ylabel('Requests per 30s')
            ax.grid(True, alpha=0.3)
            
            # Format x-axis
            plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        chart_path = os.path.join(self.output_dir, f"{report_name}_throughput.png")
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return chart_path
    
    def _create_error_chart(self, error_data: Dict, report_name: str) -> str:
        """Tạo error analysis chart"""
        fig, axes = plt.subplots(1, 2, figsize=(15, 6))
        fig.suptitle('Error Analysis', fontsize=16, fontweight='bold')
        
        # Error counts pie chart
        error_counts = error_data.get('error_counts', {})
        if error_counts:
            labels, values = zip(*error_counts.items())
            axes[0].pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
            axes[0].set_title('Error Distribution')
        
        # Errors by request type
        errors_by_type = error_data.get('errors_by_type', {})
        if errors_by_type:
            types = list(errors_by_type.keys())
            error_counts_by_type = [len(errors) for errors in errors_by_type.values()]
            
            axes[1].bar(types, error_counts_by_type, color='red', alpha=0.7)
            axes[1].set_title('Errors by Request Type')
            axes[1].set_ylabel('Number of Errors')
            axes[1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        chart_path = os.path.join(self.output_dir, f"{report_name}_errors.png")
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return chart_path
    
    def _create_system_metrics_chart(self, system_data: Dict, report_name: str) -> str:
        """Tạo system metrics chart"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('System Resource Usage', fontsize=16, fontweight='bold')
        
        metrics = ['cpu_percent', 'memory_percent', 'memory_used_gb', 'network_bytes_sent']
        titles = ['CPU Usage (%)', 'Memory Usage (%)', 'Memory Used (GB)', 'Network Sent (Bytes)']
        
        for i, (metric, title) in enumerate(zip(metrics, titles)):
            if metric in system_data:
                data = system_data[metric]
                row, col = i // 2, i % 2
                
                # Create simple bar chart with avg, max, min
                categories = ['Average', 'Maximum', 'Minimum', 'Current']
                values = [
                    data.get('avg', 0),
                    data.get('max', 0),
                    data.get('min', 0),
                    data.get('current', 0)
                ]
                
                axes[row, col].bar(categories, values, alpha=0.7)
                axes[row, col].set_title(title)
                axes[row, col].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        chart_path = os.path.join(self.output_dir, f"{report_name}_system.png")
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return chart_path
    
    def _generate_html_report(self, test_data: Dict[str, Any], 
                            charts: Dict[str, str], report_name: str) -> str:
        """Tạo HTML report"""
        
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bedrock Load Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { text-align: center; color: #333; border-bottom: 2px solid #007acc; padding-bottom: 20px; margin-bottom: 30px; }
        .section { margin-bottom: 30px; }
        .section h2 { color: #007acc; border-left: 4px solid #007acc; padding-left: 10px; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .metric-card { background-color: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid #007acc; }
        .metric-value { font-size: 24px; font-weight: bold; color: #333; }
        .metric-label { font-size: 14px; color: #666; margin-top: 5px; }
        .chart { text-align: center; margin: 20px 0; }
        .chart img { max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 4px; }
        .table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        .table th, .table td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        .table th { background-color: #007acc; color: white; }
        .table tr:hover { background-color: #f5f5f5; }
        .success { color: #28a745; }
        .error { color: #dc3545; }
        .warning { color: #ffc107; }
        .timestamp { color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Amazon Bedrock Load Test Report</h1>
            <p class="timestamp">Generated on: {{ timestamp }}</p>
            {% if test_info %}
            <p>Test Type: {{ test_info.test_type }}</p>
            {% endif %}
        </div>

        <!-- Executive Summary -->
        <div class="section">
            <h2>Executive Summary</h2>
            <div class="metrics-grid">
                {% if performance.overall %}
                <div class="metric-card">
                    <div class="metric-value">{{ performance.overall.total_requests }}</div>
                    <div class="metric-label">Total Requests</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value {{ 'success' if performance.overall.success_rate > 0.95 else 'warning' if performance.overall.success_rate > 0.8 else 'error' }}">
                        {{ "%.1f%%" | format(performance.overall.success_rate * 100) }}
                    </div>
                    <div class="metric-label">Success Rate</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{{ "%.2f" | format(performance.overall.requests_per_second) }}</div>
                    <div class="metric-label">Requests/Second</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{{ "%.2f" | format(performance.overall.test_duration) }}s</div>
                    <div class="metric-label">Test Duration</div>
                </div>
                {% endif %}
                {% if costs.costs.total %}
                <div class="metric-card">
                    <div class="metric-value">${{ "%.4f" | format(costs.costs.total) }}</div>
                    <div class="metric-label">Total Cost</div>
                </div>
                {% endif %}
            </div>
        </div>

        <!-- Performance Charts -->
        {% if charts.performance %}
        <div class="section">
            <h2>Performance Metrics</h2>
            <div class="chart">
                <img src="{{ charts.performance | basename }}" alt="Performance Metrics">
            </div>
        </div>
        {% endif %}

        <!-- Latency Analysis -->
        {% if charts.latency_dist %}
        <div class="section">
            <h2>Latency Analysis</h2>
            <div class="chart">
                <img src="{{ charts.latency_dist | basename }}" alt="Latency Distribution">
            </div>
        </div>
        {% endif %}

        <!-- Throughput Analysis -->
        {% if charts.throughput %}
        <div class="section">
            <h2>Throughput Analysis</h2>
            <div class="chart">
                <img src="{{ charts.throughput | basename }}" alt="Throughput Over Time">
            </div>
        </div>
        {% endif %}

        <!-- Cost Analysis -->
        {% if charts.costs %}
        <div class="section">
            <h2>Cost Analysis</h2>
            <div class="chart">
                <img src="{{ charts.costs | basename }}" alt="Cost Analysis">
            </div>
            
            <h3>Cost Breakdown</h3>
            <table class="table">
                <thead>
                    <tr>
                        <th>Service</th>
                        <th>Cost ($)</th>
                        <th>Percentage</th>
                    </tr>
                </thead>
                <tbody>
                    {% for service, cost in costs.costs.items() %}
                    {% if service != 'total' and cost > 0 %}
                    <tr>
                        <td>{{ service | replace('_', ' ') | title }}</td>
                        <td>${{ "%.4f" | format(cost) }}</td>
                        <td>{{ "%.1f%%" | format((cost / costs.costs.total * 100) if costs.costs.total > 0 else 0) }}</td>
                    </tr>
                    {% endif %}
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}

        <!-- Error Analysis -->
        {% if errors.total_errors > 0 %}
        <div class="section">
            <h2>Error Analysis</h2>
            {% if charts.errors %}
            <div class="chart">
                <img src="{{ charts.errors | basename }}" alt="Error Analysis">
            </div>
            {% endif %}
            
            <h3>Error Summary</h3>
            <table class="table">
                <thead>
                    <tr>
                        <th>Error Type</th>
                        <th>Count</th>
                        <th>Percentage</th>
                    </tr>
                </thead>
                <tbody>
                    {% for error_type, count in errors.error_counts.items() %}
                    <tr>
                        <td>{{ error_type }}</td>
                        <td>{{ count }}</td>
                        <td>{{ "%.1f%%" | format((count / errors.total_errors * 100) if errors.total_errors > 0 else 0) }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}

        <!-- System Metrics -->
        {% if charts.system %}
        <div class="section">
            <h2>System Resource Usage</h2>
            <div class="chart">
                <img src="{{ charts.system | basename }}" alt="System Metrics">
            </div>
        </div>
        {% endif %}

        <!-- Detailed Performance by Request Type -->
        <div class="section">
            <h2>Detailed Performance Metrics</h2>
            <table class="table">
                <thead>
                    <tr>
                        <th>Request Type</th>
                        <th>Total Requests</th>
                        <th>Success Rate</th>
                        <th>Avg Latency (s)</th>
                        <th>P95 Latency (s)</th>
                        <th>P99 Latency (s)</th>
                    </tr>
                </thead>
                <tbody>
                    {% for req_type, metrics in performance.items() %}
                    {% if req_type != 'overall' and metrics is mapping %}
                    <tr>
                        <td>{{ req_type | replace('_', ' ') | title }}</td>
                        <td>{{ metrics.total_requests }}</td>
                        <td class="{{ 'success' if metrics.success_rate > 0.95 else 'warning' if metrics.success_rate > 0.8 else 'error' }}">
                            {{ "%.1f%%" | format(metrics.success_rate * 100) }}
                        </td>
                        <td>{{ "%.3f" | format(metrics.avg_latency) }}</td>
                        <td>{{ "%.3f" | format(metrics.p95_latency) }}</td>
                        <td>{{ "%.3f" | format(metrics.p99_latency) }}</td>
                    </tr>
                    {% endif %}
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <!-- Test Configuration -->
        {% if test_info.configuration %}
        <div class="section">
            <h2>Test Configuration</h2>
            <pre style="background-color: #f8f9fa; padding: 15px; border-radius: 4px; overflow-x: auto;">{{ test_info.configuration | tojson(indent=2) }}</pre>
        </div>
        {% endif %}
    </div>
</body>
</html>
        """
        
        # Prepare template data
        template_data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'test_info': test_data.get('test_info', {}),
            'performance': test_data.get('performance', {}),
            'costs': test_data.get('costs', {}),
            'errors': test_data.get('errors', {}),
            'system_metrics': test_data.get('system_metrics', {}),
            'charts': charts
        }
        
        # Render template
        template = Template(html_template)
        html_content = template.render(**template_data)
        
        # Save HTML report
        html_path = os.path.join(self.output_dir, f"{report_name}.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return html_path
    
    def _generate_csv_reports(self, test_data: Dict[str, Any], report_name: str) -> List[str]:
        """Tạo CSV reports cho raw data"""
        csv_files = []
        
        # Request metrics CSV
        if 'raw_data' in test_data and 'request_metrics' in test_data['raw_data']:
            df = pd.DataFrame(test_data['raw_data']['request_metrics'])
            csv_path = os.path.join(self.output_dir, f"{report_name}_requests.csv")
            df.to_csv(csv_path, index=False)
            csv_files.append(csv_path)
        
        # Error metrics CSV
        if 'raw_data' in test_data and 'error_metrics' in test_data['raw_data']:
            df = pd.DataFrame(test_data['raw_data']['error_metrics'])
            csv_path = os.path.join(self.output_dir, f"{report_name}_errors.csv")
            df.to_csv(csv_path, index=False)
            csv_files.append(csv_path)
        
        return csv_files
