#!/bin/bash
# One-command setup for both backend and frontend
cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && cd ..
cd Frontend && npm install && cd ..
echo "Setup complete!"
