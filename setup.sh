#!/bin/bash

# Setup script for Bedrock Load Testing Suite
set -e

echo "🚀 Setting up Bedrock Load Testing Suite..."
echo "=========================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip first."
    exit 1
fi

echo "✅ pip3 found: $(pip3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

echo "✅ Dependencies installed successfully"

# Create reports directory
if [ ! -d "reports" ]; then
    mkdir reports
    echo "✅ Reports directory created"
fi

# Check AWS CLI
if command -v aws &> /dev/null; then
    echo "✅ AWS CLI found: $(aws --version)"
    
    # Check AWS credentials
    if aws sts get-caller-identity &> /dev/null; then
        echo "✅ AWS credentials configured"
        
        # Check Bedrock access
        if aws bedrock list-foundation-models --region us-east-1 &> /dev/null; then
            echo "✅ Bedrock access confirmed"
        else
            echo "⚠️  Bedrock access not confirmed. Please check permissions."
        fi
    else
        echo "⚠️  AWS credentials not configured. Run 'aws configure' to set up."
    fi
else
    echo "⚠️  AWS CLI not found. Please install AWS CLI for full functionality."
fi

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Configure AWS credentials (if not done): aws configure"
echo "2. Update configuration files:"
echo "   - config/test_config.yaml"
echo "   - config/models_config.yaml"
echo "3. Run demo test: make demo"
echo "4. Run full tests: make test-foundation"
echo ""
echo "For help: make help"
echo ""
echo "Happy testing! 🚀"
