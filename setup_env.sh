#!/bin/bash
# RE Market Tool - Environment Setup Script
# ===========================================
# Complete environment setup for RE project

set -e  # Exit on any error

echo "🏗️ Setting up RE Market Tool environment..."
echo "=========================================="

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $PYTHON_VERSION detected. Need Python $REQUIRED_VERSION or higher."
    exit 1
fi

echo "✅ Python $PYTHON_VERSION detected"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install production dependencies
echo "📥 Installing production dependencies..."
pip install -r requirements.txt

# Install development dependencies if requested
if [ "$1" = "--dev" ]; then
    echo "🛠️ Installing development dependencies..."
    pip install -r requirements-dev.txt
    echo "✅ Development dependencies installed"
fi

# Create activation script
echo "📝 Creating activation script..."
cat > activate.sh << 'EOF'
#!/bin/bash
# Quick activation script for RE project
echo "🚀 Activating RE Market Tool environment..."
source venv/bin/activate
echo "✅ Environment activated!"
echo "📁 Current directory: $(pwd)"
echo "🐍 Python version: $(python --version)"
echo "📦 Installed packages: $(pip list | wc -l) packages"
EOF

chmod +x activate.sh

# Create .python-version file
echo "📋 Documenting Python version..."
python --version > .python-version

# Create .gitignore
echo "📝 Creating .gitignore..."
cat > .gitignore << 'EOF'
# Virtual Environment
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# Data Files
backend/data/raw/*.csv
backend/data/processed/*.csv
backend/aggregations/*/*.json
backend/aggregations/*/*.geojson
backend/statistics/*.json

# Logs
backend/logs/*.log
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Environment
.env
.env.local
EOF

echo ""
echo "✅ Environment setup complete!"
echo "=============================="
echo "💡 Quick start commands:"
echo "   source activate.sh    # Activate environment"
echo "   python check_env.py   # Validate environment"
echo "   deactivate           # Deactivate environment"
echo ""
echo "🎯 Next steps:"
echo "   1. Run 'source activate.sh' to activate the environment"
echo "   2. Run 'python check_env.py' to validate the setup"
echo "   3. Start developing with the ETL pipeline!"
