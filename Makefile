# Makefile cho Bedrock Load Testing

.PHONY: help install demo test-foundation test-kb test-agent test-all clean

# Default target
help:
	@echo "Amazon Bedrock Load Testing Suite"
	@echo "================================="
	@echo ""
	@echo "Available commands:"
	@echo "  make install          - Install dependencies"
	@echo "  make demo            - Run demo test (3 requests)"
	@echo "  make test-foundation - Run foundation model tests"
	@echo "  make test-kb         - Run knowledge base tests"
	@echo "  make test-agent      - Run agent tests"
	@echo "  make test-all        - Run all tests"
	@echo "  make clean           - Clean up reports and logs"
	@echo ""
	@echo "Configuration:"
	@echo "  Edit config/test_config.yaml for test settings"
	@echo "  Edit config/models_config.yaml for model settings"

# Install dependencies
install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	@echo "✅ Dependencies installed"

# Run demo test
demo:
	@echo "Running demo test..."
	python demo_test.py

# Run foundation model tests
test-foundation:
	@echo "Running foundation model load tests..."
	python scripts/foundation_model_test.py

# Run knowledge base tests (requires KB_ID)
test-kb:
	@if [ -z "$(KB_ID)" ]; then \
		echo "❌ Please provide Knowledge Base ID: make test-kb KB_ID=your-kb-id"; \
		exit 1; \
	fi
	@echo "Running knowledge base tests with KB_ID=$(KB_ID)..."
	python scripts/knowledge_base_test.py --kb-id $(KB_ID)

# Run agent tests (requires AGENT_ID)
test-agent:
	@if [ -z "$(AGENT_ID)" ]; then \
		echo "❌ Please provide Agent ID: make test-agent AGENT_ID=your-agent-id"; \
		exit 1; \
	fi
	@echo "Running agent tests with AGENT_ID=$(AGENT_ID)..."
	python scripts/agent_test.py --agent-id $(AGENT_ID)

# Run all tests
test-all:
	@echo "Running comprehensive test suite..."
	@echo "⚠️  This will run foundation model tests only by default"
	@echo "⚠️  Use --enable-kb, --enable-agent flags for other tests"
	python run_all_tests.py

# Run all tests with specific services
test-all-full:
	@if [ -z "$(KB_ID)" ] || [ -z "$(AGENT_ID)" ]; then \
		echo "❌ Please provide both KB_ID and AGENT_ID:"; \
		echo "   make test-all-full KB_ID=your-kb-id AGENT_ID=your-agent-id"; \
		exit 1; \
	fi
	@echo "Running full test suite..."
	python run_all_tests.py --enable-kb --kb-id $(KB_ID) --enable-agent --agent-id $(AGENT_ID)

# Clean up
clean:
	@echo "Cleaning up reports and logs..."
	rm -rf reports/*.json
	rm -rf reports/*.html
	rm -rf reports/*.png
	rm -rf reports/*.csv
	rm -f *.log
	@echo "✅ Cleanup completed"

# Check AWS credentials
check-aws:
	@echo "Checking AWS credentials and Bedrock access..."
	@python -c "
import boto3
try:
    session = boto3.Session()
    creds = session.get_credentials()
    if creds:
        print('✅ AWS credentials found')
        bedrock = session.client('bedrock', region_name='us-east-1')
        bedrock.list_foundation_models()
        print('✅ Bedrock access confirmed')
    else:
        print('❌ AWS credentials not found')
        exit(1)
except Exception as e:
    print(f'❌ Error: {e}')
    exit(1)
"

# Setup configuration files
setup-config:
	@echo "Setting up configuration files..."
	@if [ ! -f config/test_config.yaml ]; then \
		echo "✅ config/test_config.yaml already exists"; \
	fi
	@if [ ! -f config/models_config.yaml ]; then \
		echo "✅ config/models_config.yaml already exists"; \
	fi
	@echo "⚠️  Please update the configuration files with your specific settings:"
	@echo "   - Knowledge Base ID in config/models_config.yaml"
	@echo "   - Agent ID in config/models_config.yaml"
	@echo "   - Guardrail ID in config/models_config.yaml"

# Show current configuration
show-config:
	@echo "Current Configuration:"
	@echo "====================="
	@echo ""
	@echo "Test Config (config/test_config.yaml):"
	@head -20 config/test_config.yaml
	@echo ""
	@echo "Models Config (config/models_config.yaml):"
	@head -20 config/models_config.yaml

# Validate configuration
validate-config:
	@echo "Validating configuration files..."
	@python -c "
import yaml
try:
    with open('config/test_config.yaml', 'r') as f:
        yaml.safe_load(f)
    print('✅ test_config.yaml is valid')
    
    with open('config/models_config.yaml', 'r') as f:
        yaml.safe_load(f)
    print('✅ models_config.yaml is valid')
except Exception as e:
    print(f'❌ Configuration error: {e}')
    exit(1)
"

# Quick start guide
quickstart:
	@echo "Bedrock Load Testing Quick Start"
	@echo "==============================="
	@echo ""
	@echo "1. Install dependencies:"
	@echo "   make install"
	@echo ""
	@echo "2. Check AWS credentials:"
	@echo "   make check-aws"
	@echo ""
	@echo "3. Run demo test:"
	@echo "   make demo"
	@echo ""
	@echo "4. Run foundation model tests:"
	@echo "   make test-foundation"
	@echo ""
	@echo "5. For Knowledge Base tests:"
	@echo "   make test-kb KB_ID=your-knowledge-base-id"
	@echo ""
	@echo "6. For Agent tests:"
	@echo "   make test-agent AGENT_ID=your-agent-id"
	@echo ""
	@echo "7. Clean up when done:"
	@echo "   make clean"
