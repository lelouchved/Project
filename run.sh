#!/usr/bin/env bash
# MSOT Club Activities & Governance Tracker - One-Command Setup & Launch
set -e

echo "=========================================================="
echo "  MSOT CLUB ACTIVITIES & GOVERNANCE TRACKER"
echo "  Problem 3 Challenge Submission"
echo "=========================================================="

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is required but was not found."
    exit 1
fi

echo "✔ Detected Python $(python3 --version)"

# 2. Setup Virtual Environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# 3. Install Dependencies
echo "📦 Installing / verifying dependencies..."
./venv/bin/pip install -q --upgrade pip
./venv/bin/pip install -q -r requirements.txt

# 4. Seed Database if fresh
if [ ! -f "club_tracker.db" ]; then
    echo "🌱 Seeding initial database (4 campuses, clubs, users)..."
    PYTHONPATH=. ./venv/bin/python -m backend.seed_data
else
    echo "✔ Existing database detected (club_tracker.db)."
fi

# 5. Launch FastAPI Server
echo ""
echo "🚀 Starting MSOT Club Tracker Server on http://localhost:8000"
echo "📄 Swagger API Documentation at: http://localhost:8000/docs"
echo "🔍 Public Verification Gateway at: http://localhost:8000/verify/{cert_id}"
echo ""
echo "Press Ctrl+C to terminate."
echo "=========================================================="

PYTHONPATH=. ./venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
