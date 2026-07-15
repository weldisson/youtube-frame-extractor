#!/bin/bash
# Activate virtual environment and start the web application
echo "Starting YouTube Frame Extractor..."
source venv/bin/activate
python3 -m app.main
