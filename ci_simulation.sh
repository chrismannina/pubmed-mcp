#!/bin/bash
# Complete CI/CD Pipeline Simulation Script

echo "🔧 Simulating CI/CD Pipeline Locally..."
echo ""

echo "📦 Step 1: Install dependencies"
pip install pytest pytest-asyncio black isort mypy flake8 --quiet

echo "✅ Step 2: Check code formatting"
black --check --diff src/ tests/ || (echo "❌ Code formatting issues found" && exit 1)

echo "🔍 Step 3: Run linting"
flake8 src/ tests/ --quiet || (echo "❌ Linting issues found" && exit 1)

echo "🧪 Step 4: Run tests"
python -m pytest tests/ -v --tb=short -x || (echo "❌ Tests failed" && exit 1)

echo "📦 Step 5: Test package installation"
pip install -e . --quiet
python -c "import src; print('✅ Package imports successfully')"

echo ""
echo "🎉 CI/CD Pipeline simulation completed successfully!"
