# Contributing to Bedrock Load Testing Suite

Cảm ơn bạn quan tâm đến việc đóng góp cho Bedrock Load Testing Suite! 

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- AWS CLI configured
- AWS Bedrock access
- Git

### Setup Development Environment

1. Clone repository:
```bash
git clone <repository-url>
cd bedrock-load-testing
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
make install
```

4. Verify setup:
```bash
make check-aws
make demo
```

## 🛠️ Development Guidelines

### Code Style
- Follow PEP 8 for Python code
- Use type hints where possible
- Add docstrings for all functions and classes
- Keep functions focused and small

### Testing
- Test your changes with demo test first
- Run foundation model tests before submitting
- Ensure no regression in existing functionality
- Add new test cases for new features

### Documentation
- Update README.md for new features
- Add docstrings for new functions
- Update configuration examples
- Include usage examples

## 📝 How to Contribute

### Reporting Bugs
1. Check existing issues first
2. Create detailed bug report with:
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details
   - Error messages/logs

### Suggesting Features
1. Check existing feature requests
2. Create feature request with:
   - Clear description
   - Use case/motivation
   - Proposed implementation (if any)

### Submitting Changes
1. Fork the repository
2. Create feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes
4. Test thoroughly
5. Commit with clear messages
6. Push to your fork
7. Create pull request

### Commit Message Format
```
type(scope): brief description

Detailed explanation if needed

- List of changes
- Breaking changes (if any)
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## 🧪 Testing Your Changes

### Before Submitting
```bash
# Run demo test
make demo

# Run foundation model tests
make test-foundation

# Validate configuration
make validate-config

# Check code style (if you have linting tools)
flake8 .
black --check .
```

### Test Coverage Areas
- Foundation model testing
- Knowledge base testing
- Agent testing (if applicable)
- Metrics collection
- Report generation
- Error handling
- Cost calculation

## 📋 Pull Request Checklist

- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
- [ ] Commit messages are clear
- [ ] PR description explains changes

## 🔧 Adding New Features

### New Model Support
1. Update `config/models_config.yaml`
2. Add model-specific request/response handling
3. Update cost calculations
4. Add test cases

### New Test Types
1. Create new script in `scripts/`
2. Follow existing patterns
3. Add to `run_all_tests.py`
4. Update Makefile
5. Document usage

### New Metrics
1. Update `MetricsCollector` class
2. Add to report generation
3. Update HTML templates
4. Test visualization

## 🐛 Debugging

### Common Issues
- AWS credentials not configured
- Bedrock permissions missing
- Rate limiting/throttling
- Cost accumulation

### Debug Tools
- Enable debug logging: `logging.basicConfig(level=logging.DEBUG)`
- Use `--verbose` flags where available
- Check CloudWatch logs
- Monitor AWS costs

## 📚 Resources

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Boto3 Bedrock Reference](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock.html)
- [Python Best Practices](https://pep8.org/)

## 🤝 Community

- Be respectful and inclusive
- Help others learn
- Share knowledge and experiences
- Follow code of conduct

## 📄 License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to make Bedrock Load Testing Suite better! 🎉
