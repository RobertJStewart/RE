#!/bin/bash
# RE Market Tool Frontend Startup Script
# ======================================

echo "🚀 Starting RE Market Tool Frontend Server..."

# Check if we're in the right directory
if [ ! -f "frontend_script.py" ]; then
    echo "❌ Error: Please run this script from the frontend directory"
    exit 1
fi

# Check if backend virtual environment exists
if [ ! -d "../venv" ]; then
    echo "❌ Error: Backend virtual environment not found."
    echo "   Please run setup_env.sh from the project root first."
    exit 1
fi

echo "✅ Using backend virtual environment..."
source ../venv/bin/activate

# Verify Flask is installed
if ! python -c "import flask" 2>/dev/null; then
    echo "📦 Installing Flask dependencies..."
    pip install flask flask-cors
fi

# Start the frontend server
echo "🌐 Starting frontend server on http://localhost:5000"
echo "📊 Press Ctrl+C to stop the server"
echo ""

python frontend_script.py --host localhost --port 5000 --debug
