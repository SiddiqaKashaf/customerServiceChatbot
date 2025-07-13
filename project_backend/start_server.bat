@echo off
echo Starting TechCorp Solutions RAG Chatbot Server...
echo.

REM Set environment variables
set FLASK_SECRET_KEY=your-secret-key-here-12345
set FLASK_DEBUG=False

REM Start the production server
python run_production.py

pause 