# Amazon Bedrock Load Testing Suite

Bộ công cụ load testing toàn diện cho Amazon Bedrock, bao gồm testing cho Foundation Models, Knowledge Bases, Agents và các tính năng khác.

## Cấu trúc thư mục

```
bedrock-load-testing/
├── README.md                          # Tài liệu hướng dẫn
├── requirements.txt                   # Dependencies Python
├── config/
│   ├── test_config.yaml              # Cấu hình test chung
│   └── models_config.yaml            # Cấu hình các models
├── scripts/
│   ├── foundation_model_test.py      # Test Foundation Models
│   ├── knowledge_base_test.py        # Test Knowledge Bases
│   ├── agent_test.py                 # Test Bedrock Agents
│   ├── batch_inference_test.py       # Test Batch Inference
│   └── guardrails_test.py           # Test Guardrails
├── data/
│   ├── test_prompts.json            # Prompts mẫu cho testing
│   ├── knowledge_base_queries.json  # Queries cho KB testing
│   └── agent_scenarios.json        # Scenarios cho Agent testing
├── utils/
│   ├── __init__.py
│   ├── bedrock_client.py           # Bedrock client wrapper
│   ├── metrics_collector.py        # Thu thập metrics
│   └── report_generator.py         # Tạo báo cáo
└── reports/                        # Thư mục chứa báo cáo kết quả

```

## Cài đặt

1. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

2. Cấu hình AWS credentials:
```bash
aws configure
```

3. Cập nhật file cấu hình trong thư mục `config/`

## Các loại test

### 1. Foundation Model Load Test
- Test throughput và latency của các foundation models
- Test với các kích thước prompt khác nhau
- Test concurrent requests
- Monitoring token usage và costs

### 2. Knowledge Base Load Test
- Test query performance
- Test concurrent searches
- Test với các loại queries khác nhau
- Monitoring OCU usage

### 3. Agent Load Test
- Test agent conversations
- Test action group invocations
- Test complex workflows
- End-to-end performance testing

### 4. Batch Inference Test
- Test batch processing capabilities
- Large-scale data processing
- Cost optimization testing

### 5. Guardrails Test
- Test content filtering performance
- Test policy enforcement
- Impact on latency và throughput

## Chạy tests

### Test đơn lẻ:
```bash
python scripts/foundation_model_test.py
python scripts/knowledge_base_test.py
python scripts/agent_test.py
```

### Test suite hoàn chỉnh:
```bash
python run_all_tests.py
```

## Metrics được thu thập

- **Performance Metrics**: Latency, throughput, success rate
- **Cost Metrics**: Token usage, request costs, OCU usage
- **Error Metrics**: Error rates, timeout rates, throttling
- **Resource Metrics**: CPU, memory, network usage

## Báo cáo

Các báo cáo được tạo tự động trong thư mục `reports/`:
- Performance summary
- Cost analysis
- Error analysis
- Recommendations

## Best Practices

1. **Gradual Load Increase**: Bắt đầu với load thấp và tăng dần
2. **Monitor Costs**: Theo dõi chi phí trong quá trình test
3. **Test in Non-Production**: Sử dụng environment riêng biệt
4. **Cleanup Resources**: Dọn dẹp resources sau khi test
5. **Document Results**: Lưu trữ kết quả để so sánh

## Lưu ý quan trọng

- ⚠️ **Chi phí**: Load testing có thể tạo ra chi phí đáng kể
- ⚠️ **Rate Limits**: Chú ý các giới hạn của AWS Bedrock
- ⚠️ **Regions**: Test trong region phù hợp
- ⚠️ **Cleanup**: Luôn cleanup resources sau khi test
