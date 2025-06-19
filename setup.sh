#!/bin/bash
echo "🚀 Setting up C++ Study Tracker..."

# Install dependencies
echo "📦 Installing dependencies..."
uv sync

# Run tests
echo "🧪 Running tests..."
uv run pytest

echo "✅ Setup complete! Run 'uv run study' to start tracking."