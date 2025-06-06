# Cập nhật Code để sử dụng AWS Bedrock Inference Profiles

## Tổng quan

Code đã được cập nhật thành công để sử dụng **AWS Bedrock Inference Profiles** thay vì gọi trực tiếp model ID. Điều này giải quyết lỗi `ValidationException` khi gọi các model mới như Claude 3.5 Sonnet v2.

## Lỗi ban đầu

```
ValidationException: Invocation of model ID anthropic.claude-3-5-sonnet-20241022-v2:0 with on-demand throughput isn't supported. Retry your request with the ID or ARN of an inference profile that contains this model.
```

## Giải pháp

### 1. Cập nhật Model Configuration (`config/models_config.yaml`)

**Trước:**
```yaml
claude_3_5_sonnet:
  model_id: "anthropic.claude-3-5-sonnet-20241022-v2:0"  # ❌ Model ID trực tiếp
```

**Sau:**
```yaml
claude_3_5_sonnet_v2:
  model_id: "us.anthropic.claude-3-5-sonnet-20241022-v2:0"  # ✅ Inference Profile ID
  display_name: "Claude 3.5 Sonnet v2"
  request_format: "anthropic"
```

### 2. Cập nhật Bedrock Client (`utils/bedrock_client.py`)

#### Tính năng mới:
- **Multi-format support**: Hỗ trợ nhiều định dạng request (Anthropic, Llama, Nova, DeepSeek, Mistral)
- **Automatic request formatting**: Tự động format request body dựa trên model type
- **Enhanced response parsing**: Parse response từ các model khác nhau
- **Cost calculation**: Tính toán chi phí tự động
- **Model management**: Quản lý model qua tên thay vì ID

#### Phương thức mới:
```python
# Gọi model bằng tên từ config
result = client.invoke_model_by_name("claude_3_5_sonnet_v2", "Hello!")

# Liệt kê models có sẵn
models = client.list_available_models()

# Lấy thông tin model
info = client.get_model_info("claude_3_5_sonnet_v2")
```

### 3. Cập nhật Demo Script (`demo_test.py`)

- Sử dụng `invoke_model_by_name()` thay vì `invoke_model()`
- Hiển thị thông tin chi tiết về models có sẵn
- Test nhiều models khác nhau
- Tính toán chi phí chính xác

## Models được hỗ trợ

### Claude Models (Anthropic)
- `claude_3_5_sonnet_v2`: us.anthropic.claude-3-5-sonnet-20241022-v2:0
- `claude_3_5_sonnet_v1`: us.anthropic.claude-3-5-sonnet-20240620-v1:0
- `claude_3_5_haiku`: us.anthropic.claude-3-5-haiku-20241022-v1:0
- `claude_3_sonnet`: us.anthropic.claude-3-sonnet-20240229-v1:0
- `claude_3_haiku`: us.anthropic.claude-3-haiku-20240307-v1:0
- `claude_3_opus`: us.anthropic.claude-3-opus-20240229-v1:0

### Llama Models (Meta)
- `llama3_2_90b`: us.meta.llama3-2-90b-instruct-v1:0
- `llama3_2_11b`: us.meta.llama3-2-11b-instruct-v1:0
- `llama3_2_3b`: us.meta.llama3-2-3b-instruct-v1:0
- `llama3_2_1b`: us.meta.llama3-2-1b-instruct-v1:0
- `llama3_1_8b`: us.meta.llama3-1-8b-instruct-v1:0
- `llama3_1_70b`: us.meta.llama3-1-70b-instruct-v1:0
- `llama3_3_70b`: us.meta.llama3-3-70b-instruct-v1:0

### Nova Models (Amazon)
- `nova_lite`: us.amazon.nova-lite-v1:0
- `nova_micro`: us.amazon.nova-micro-v1:0
- `nova_pro`: us.amazon.nova-pro-v1:0
- `nova_premier`: us.amazon.nova-premier-v1:0

### Các Models khác
- `deepseek_r1`: us.deepseek.r1-v1:0
- `mistral_pixtral_large`: us.mistral.pixtral-large-2502-v1:0

## Kết quả Test

### Test thành công với Claude 3.5 Sonnet v2:
```
✅ SUCCESS!
   Latency: 3.425s
   Input tokens: 21
   Output tokens: 61
   Cost: $0.000978
```

### Test nhiều models:
```
✅ claude_3_5_sonnet_v2: 1.826s, $0.000129
✅ claude_3_5_haiku: 0.897s, $0.000034
✅ nova_lite: 0.420s, $0.000003
✅ llama3_2_1b: 0.539s, $0.000004

Success Rate: 4/4 (100.0%)
Total Cost: $0.000170
```

## Cách sử dụng

### 1. Chạy demo cơ bản:
```bash
cd bedrock-load-testing
source myenv/bin/activate
python demo_test.py
```

### 2. Test code đã cập nhật:
```bash
python test_updated_demo.py
```

### 3. Sử dụng trong code:
```python
from utils.bedrock_client import BedrockClient

client = BedrockClient(region="us-east-1")

# Gọi model bằng tên
result = client.invoke_model_by_name(
    model_name="claude_3_5_sonnet_v2",
    prompt="Hello, world!"
)

print(f"Response: {result['response_text']}")
print(f"Cost: ${result['cost']['total_cost']:.6f}")
```

## Lợi ích

1. **Tương thích với models mới**: Hỗ trợ tất cả models yêu cầu inference profiles
2. **Đơn giản hóa việc sử dụng**: Gọi model bằng tên thay vì ID phức tạp
3. **Tính toán chi phí tự động**: Không cần tính toán thủ công
4. **Hỗ trợ đa định dạng**: Tự động format request cho từng loại model
5. **Dễ bảo trì**: Cấu hình tập trung trong YAML file

## Lưu ý quan trọng

- ⚠️ **Inference Profiles chỉ hoạt động trong một số regions**: us-east-1, us-west-2, us-east-2
- ⚠️ **Chi phí có thể khác nhau**: Kiểm tra pricing mới nhất từ AWS
- ⚠️ **Rate limits**: Inference profiles có thể có rate limits khác nhau
- ⚠️ **Availability**: Một số models có thể không available trong tất cả regions

## Tài liệu tham khảo

- [AWS Bedrock Inference Profiles Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles.html)
- [AWS Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/)
- [Anthropic Claude Models](https://docs.anthropic.com/claude/docs/models-overview)
