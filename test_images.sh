#!/bin/bash

# Test script for Obsidian MCP image handling

echo "Starting Obsidian MCP Image Handling Tests..."
echo "==========================================="
echo ""

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
else
    echo "No virtual environment found, using system Python"
fi

# Check for API key
if [ -z "$OBSIDIAN_REST_API_KEY" ]; then
    echo "ERROR: OBSIDIAN_REST_API_KEY environment variable not set!"
    echo ""
    echo "To set it:"
    echo "  export OBSIDIAN_REST_API_KEY='your-api-key-here'"
    echo ""
    echo "Get your API key from Obsidian:"
    echo "  Settings > Community plugins > Local REST API"
    exit 1
fi

# Run the test
echo "Running image handling tests..."
echo ""
python tests/test_image_handling.py

echo ""
echo "Test completed!"